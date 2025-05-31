use std::{io, sync::mpsc, thread};
use std::time::Duration;
use crossterm::event::{KeyCode, KeyEventKind};
use ratatui::{
    layout::{Constraint, Layout},
    prelude::{Buffer, Rect},
    style::{Color, Stylize},
    text::Line,
    widgets::{Block, Widget, Borders},
    widgets::canvas::{Canvas, Rectangle},
    DefaultTerminal, Frame,
};

fn main() -> io::Result<()> {
    let mut terminal  = ratatui::init();

    let (main_tx, main_rx) = mpsc::channel::<Event>();
    let (move_tx, move_rx) = mpsc::channel::<Event>();

    let tx_to_input_events = main_tx.clone();
    thread::spawn(move || {
        handle_input_events(tx_to_input_events);
    });

    let tx_to_background_position_events = main_tx.clone();
    thread::spawn(move || {
        run_background_thread(tx_to_background_position_events, move_rx);
    });

    let mut app = App{
        exit:false,
        robot_pos: (10.0, 5.0),
        path: vec![(10.0, 5.0)],
        robot_size: (10.0, 5.0),
         };

    let app_result = app.run(&mut terminal, main_rx, move_tx);

    ratatui::restore();
    app_result
}

enum Event {
    Input(crossterm::event::KeyEvent),
    PositionChange(f64, f64),
    MoveInstruction((i32, i32)),
}

fn handle_input_events(tx: mpsc::Sender<Event>) {
    loop {
        match crossterm::event::read().unwrap() {
            crossterm::event::Event::Key(key_event) => tx.send(Event::Input(key_event)).unwrap(),
            _ => {}
        }
    }
}

fn run_background_thread(tx: mpsc::Sender<Event>, rx: mpsc::Receiver<Event>) {
    loop {
        match rx.recv().unwrap() {
            Event::MoveInstruction((dx, dy)) => {
                let (x_change, y_change);

                thread::sleep(Duration::from_millis(100)); // nasze obliczenia,
                // teraz jak sie trzyma przycisk to sygnały się stackują w trakcie sleepa i robot później
                // jedzie sam do przodu
                let speed = 0.2;

                match (dx, dy) {
                    (-1, 0) => (x_change, y_change) = (-speed, 0.0),
                    (1, 0) => (x_change, y_change) = (speed, 0.0),
                    (0, -1) => (x_change, y_change) = (0.0, speed),
                    (0, 1) => (x_change, y_change) = (0.0, -speed),
                    _ => (x_change, y_change) = (0.0, 0.0),
                }

                tx.send(Event::PositionChange(x_change, y_change)).unwrap();
            },
            _ => {}
        }
    }
}

pub struct App{
    exit: bool,
    robot_pos: (f64, f64),
    path: Vec<(f64, f64)>,
    robot_size: (f64, f64),
}

impl App{
    fn run(&mut self, terminal: &mut DefaultTerminal, rx: mpsc::Receiver<Event>, background_tx: mpsc::Sender<Event>) -> io::Result<()> {
        while !self.exit {
            match rx.recv().unwrap() {
                Event::Input(key_event) => self.handle_key_event(key_event, &background_tx)?,
                Event::PositionChange(x, y) => {
                    self.robot_pos = (self.robot_pos.0 + x, self.robot_pos.1 + y);
                    self.path.push(self.robot_pos);
                }
                _ => {},
            }
            terminal.draw(|frame| self.draw(frame))?;
        }
        Ok(())
    }

    fn draw(&self, frame: &mut Frame){
        frame.render_widget(self, frame.area());
    }

    fn handle_key_event(&mut self, key_event: crossterm::event::KeyEvent, background_tx: &mpsc::Sender<Event>) -> io::Result<()> {
        if key_event.kind == KeyEventKind::Press || key_event.kind == KeyEventKind::Repeat {
            match key_event.code {
                KeyCode::Char('q') => self.exit = true,
                KeyCode::Left => background_tx.send(Event::MoveInstruction((-1, 0))).unwrap(),
                KeyCode::Right => background_tx.send(Event::MoveInstruction((1, 0))).unwrap(),
                KeyCode::Up => background_tx.send(Event::MoveInstruction((0, -1))).unwrap(),
                KeyCode::Down => background_tx.send(Event::MoveInstruction((0, 1))).unwrap(),
                _ => {}
            }
        }
        Ok(())
    }
}

impl Widget for &App{
    fn render(self, area: Rect, buf: &mut Buffer)
    where
        Self: Sized
    {
        let vertical_layout = Layout::vertical([Constraint::Percentage(5), Constraint::Percentage(95)]);
        let [title_area, map_area] = vertical_layout.areas(area);
        Line::from("Robot route mapper").bold().render(title_area, buf);

        let (robot_new_x, robot_new_y) = (
            -self.robot_size.0/2.0 + self.robot_pos.0,
            -self.robot_size.1/2.0 + self.robot_pos.1,
        );

        let robot = Rectangle {
            x: robot_new_x,
            y: robot_new_y,
            width: self.robot_size.0,
            height: self.robot_size.1,
            color: Color::Blue,
        };

        let canvas = Canvas::default()
            .block(Block::default().borders(Borders::ALL).title("Map"))
            .paint(|ctx| {
                ctx.draw(&robot);

                for window in self.path.windows(2) {
                    let [(x1, y1), (x2, y2)] = [window[0], window[1]] else { continue; };
                    ctx.draw(&ratatui::widgets::canvas::Line {
                        x1,
                        y1,
                        x2,
                        y2,
                        color: Color::Yellow,
                    });
                }
            })
            .x_bounds([map_area.left() as f64, map_area.right() as f64])
            .y_bounds([map_area.top() as f64, map_area.bottom() as f64]);

        canvas.render(map_area, buf);
    }
}