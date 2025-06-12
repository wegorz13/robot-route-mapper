use std::{io, sync::mpsc, thread};
use crossterm::event::{KeyCode, KeyEventKind};
use reqwest::blocking::{Client};
use ratatui::{
    layout::{Constraint, Layout},
    prelude::{Buffer, Rect},
    style::{Color, Stylize},
    text::Line,
    widgets::{Block, Widget, Borders},
    widgets::canvas::{Canvas, Rectangle},
    DefaultTerminal, Frame,
};
use serde::{Deserialize, Serialize};

const ROBOT_SIZE:(f64, f64) = (10.0, 5.0);
static ADDRESS:&str ="localhost:3000";
// Program tworzy aplikację terminalową, która symuluje ruch robota i rysuje jego ścieżkę na mapie
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
        robot_size: ROBOT_SIZE,
    };

    let app_result = app.run(&mut terminal, main_rx, move_tx);

    ratatui::restore();
    app_result
}

enum Event {
    Input(crossterm::event::KeyEvent),
    PositionChange(f64, f64),
    MoveInstruction(String),
}

fn handle_input_events(tx: mpsc::Sender<Event>) {
    loop {
        match crossterm::event::read().unwrap() {
            crossterm::event::Event::Key(key_event) => tx.send(Event::Input(key_event)).unwrap(),
            _ => {}
        }
    }
}

#[derive(Serialize, Deserialize)]
struct RobotResponse {
    command: Option<String>,
    status: String,
    time: Option<f64>,
    message: Option<String>,
}

fn run_background_thread(tx: mpsc::Sender<Event>, rx: mpsc::Receiver<Event>) {
    let http_client =  Client::new();
    let fwd_bwd_speed = 56.5/18.0* ROBOT_SIZE.0;
    let lf_rt_speed = 20.0/12.0*ROBOT_SIZE.0;
    let mut last_move = String::from("none");
    loop {
        match rx.recv().unwrap() {
            Event::MoveInstruction(new_move) => {
                if last_move!=new_move{
                    let query_params =  [("cmd", "stop")];
                    let response  = http_client.get( format!("http://{}/drive",ADDRESS))
                        .query(&query_params)
                        .send()
                        .unwrap();
                    let res_obj: RobotResponse = serde_json::from_str(response.text().unwrap().as_str()).unwrap();

                    let  ( mut x_change, mut y_change) = (0.0,0.0);
                    if res_obj.status == "stopped"{
                        match res_obj.command.unwrap().as_str() {
                            "left" => (x_change, y_change) = (-lf_rt_speed*res_obj.time.unwrap(), 0.0),
                            "right" => (x_change, y_change) = (lf_rt_speed*res_obj.time.unwrap(), 0.0),
                            "forward" => (x_change, y_change) = (0.0, fwd_bwd_speed*res_obj.time.unwrap()),
                            "backward"=> (x_change, y_change) = (0.0, -fwd_bwd_speed*res_obj.time.unwrap()),
                            _ => (x_change, y_change) = (0.0, 0.0),
                        }
                    }
                    last_move = String::from("none");
                    tx.send(Event::PositionChange(x_change, y_change));
                }
                else if last_move == "none"{
                    let query_params =  [("cmd", new_move.as_str())];
                    let response  = http_client.get( format!("http://{}/drive",ADDRESS))
                        .query(&query_params)
                        .send()
                        .unwrap();

                    let res_obj: RobotResponse = serde_json::from_str(response.text().unwrap().as_str()).unwrap();
                    last_move = String::from(res_obj.command.unwrap_or("none".to_string()).as_str());
                    
                } 
            },
            _ => {
                if last_move!="none"{
                    let query_params =  [("cmd", "stop")];
                    let response  = http_client.get( format!("http://{}/drive",ADDRESS))
                        .query(&query_params)
                        .send()
                        .unwrap();
                    let res_obj: RobotResponse = serde_json::from_str(response.text().unwrap().as_str()).unwrap();

                    let  ( mut x_change, mut y_change) = (0.0,0.0);
                    if res_obj.status == "stopped"{
                        match res_obj.command.unwrap().as_str() {
                            "left" => (x_change, y_change) = (-lf_rt_speed*res_obj.time.unwrap(), 0.0),
                            "right" => (x_change, y_change) = (lf_rt_speed*res_obj.time.unwrap(), 0.0),
                            "forward" => (x_change, y_change) = (0.0, fwd_bwd_speed*res_obj.time.unwrap()),
                            "backward"=> (x_change, y_change) = (0.0, -fwd_bwd_speed*res_obj.time.unwrap()),
                            _ => (x_change, y_change) = (0.0, 0.0),
                        }
                    }
                    last_move = String::from("none");
                    tx.send(Event::PositionChange(x_change, y_change)).unwrap();   
                }
            }
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
                KeyCode::Left => background_tx.send(Event::MoveInstruction(String::from("left"))).unwrap(),
                KeyCode::Right => background_tx.send(Event::MoveInstruction(String::from("right"))).unwrap(),
                KeyCode::Up => background_tx.send(Event::MoveInstruction(String::from("forward"))).unwrap(),
                KeyCode::Down => background_tx.send(Event::MoveInstruction(String::from("backward"))).unwrap(),
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