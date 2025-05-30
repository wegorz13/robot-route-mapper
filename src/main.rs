use std::{io, sync::mpsc, thread, time::Duration};

use crossterm::event::{KeyCode, KeyEventKind};
use ratatui::{
    layout::{Constraint, Layout},
    prelude::{Buffer, Rect},
    style::{Color, Style, Stylize},
    symbols::border,
    text::Line,
    widgets::{Block, Gauge, Widget},
    widgets::canvas::Canvas,
    DefaultTerminal, Frame,
};
use ratatui::layout::Position;
use ratatui::widgets::Borders;
use ratatui::widgets::canvas::Rectangle;

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

    let mut app = App{exit:false};

    let app_result = app.run(&mut terminal, main_rx, move_tx);

    ratatui::restore();
    app_result
}

enum Event {
    Input(crossterm::event::KeyEvent),
    Position(f64, f64),
    MoveInstruction((i32, i32), (f64, f64)),
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
            Event::Position(x, y) => {
                // do some computations
                let new_position = (x, y);
                tx.send(Event::Position(new_position.0, new_position.1)).unwrap();
            },
            _ => {}
        }
    }
}

pub struct App{
    exit: bool,
}

impl App{
    fn run(&mut self, terminal: &mut DefaultTerminal, rx: mpsc::Receiver<Event>, background_tx: mpsc::Sender<Event>) -> io::Result<()> {
        while !self.exit {
            match rx.recv().unwrap() {
                Event::Input(key_event) => self.handle_key_event(key_event, &background_tx)?,
                Event::Position(x, y) => {}
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
                KeyCode::Left => {},
                KeyCode::Right => {},
                KeyCode::Up => {},
                KeyCode::Down => {},
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

        let robot = Rectangle {
            x: (map_area.left() + map_area.width / 2) as f64,
            y: (map_area.top() + map_area.height / 2) as f64,
            width: 10.0,
            height: 5.0,
            color: Color::Blue,
        };

        let canvas = Canvas::default()
            .block(Block::default().borders(Borders::ALL).title("Map"))
            .paint(|ctx| {
                ctx.draw(&robot);
            })
            .x_bounds([map_area.left() as f64, map_area.right() as f64])
            .y_bounds([map_area.top() as f64, map_area.bottom() as f64]);

        canvas.render(map_area, buf);
    }
}