import os, csv
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.utils import platform

# dla Androida/iOS
try:
    from plyer import vibrator, storagepath
    has_vibrator = True
except ImportError:
    has_vibrator = False
    vibrator = None
    storagepath = None

KV = '''
ScreenManager:
    StartScreen:
    SurveyScreen:
    LogsScreen:

<StartScreen>:
    name: "start"
    BoxLayout:
        orientation: "vertical"
        padding: 30
        spacing: 20

        Label:
            text: "ISA Workload Assessment"
            font_size: "24sp"

        Button:
            text: "Start badania"
            font_size: "20sp"
            size_hint_y: None
            height: "60dp"
            on_release: root.prompt_name()

        Button:
            text: "Sprawdź logi"
            size_hint_y: None
            height: "50dp"
            on_release:
                root.manager.get_screen('logs').load_logs()
                root.manager.current = 'logs'

        Button:
            text: "Wyjście"
            size_hint_y: None
            height: "50dp"
            on_release: app.stop()

<SurveyScreen>:
    name: "survey"
    lamp_on: app.lamp_on
    lamp_off: app.lamp_off

    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10

        RelativeLayout:
            size_hint_y: None
            height: "150dp"

            Image:
                id: lamp
                source: root.lamp_off
                size_hint: None, None
                size: "100dp", "100dp"
                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                allow_stretch: True

        Button:
            text: "VERY HIGH (5)"
            font_size: "24sp"
            on_release: root.record("5")

        Button:
            text: "HIGH (4)"
            font_size: "24sp"
            on_release: root.record("4")

        Button:
            text: "FAIR (3)"
            font_size: "24sp"
            on_release: root.record("3")

        Button:
            text: "LOW (2)"
            font_size: "24sp"
            on_release: root.record("2")

        Button:
            text: "VERY LOW (1)"
            font_size: "24sp"
            on_release: root.record("1")

        Button:
            text: "Koniec badania"
            size_hint_y: None
            height: "50dp"
            on_release: root.confirm_end()

<LogsScreen>:
    name: "logs"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10

        Spinner:
            id: spinner
            text: "Wybierz badanie"
            values: []
            size_hint_y: None
            height: "50dp"
            on_text: root.show_logs(self.text)

        ScrollView:
            GridLayout:
                id: log_box
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: 5

        Button:
            text: "Powrót"
            size_hint_y: None
            height: "50dp"
            on_release: root.manager.current = 'start'
'''

class StartScreen(Screen):
    def prompt_name(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        ti = TextInput(hint_text="Nazwa badania", multiline=False)
        btn = Button(text="OK", size_hint_y=None, height="40dp")
        box.add_widget(ti)
        box.add_widget(btn)
        pop = Popup(title="Podaj nazwę badania",
                    content=box, size_hint=(0.8, 0.4), auto_dismiss=False)
        def on_ok(_):
            name = ti.text.strip()
            if name:
                s = self.manager.get_screen('survey')
                s.start_survey(name)
                pop.dismiss()
                self.manager.current = 'survey'
        btn.bind(on_release=on_ok)
        pop.open()

class SurveyScreen(Screen):
    lamp_on = StringProperty()
    lamp_off = StringProperty()

    def start_survey(self, name):
        self.study = name
        self.responses = []
        self.ids.lamp.source = self.lamp_off
        if hasattr(self, 'blink_event'):
            self.blink_event.cancel()
        self.blink_event = Clock.schedule_interval(self._trigger_blink, 10)

    def _trigger_blink(self, dt):
        if has_vibrator and vibrator:
            try:
                vibrator.vibrate(0.5)
            except Exception:
                pass
        self.blink_event2 = Clock.schedule_interval(self._toggle_lamp, 0.7)
        Clock.schedule_once(self._stop_blink, 7)

    def _toggle_lamp(self, dt):
        lamp = self.ids.lamp
        lamp.source = self.lamp_on if lamp.source == self.lamp_off else self.lamp_off

    def _stop_blink(self, dt):
        if hasattr(self, 'blink_event2'):
            self.blink_event2.cancel()
        self.ids.lamp.source = self.lamp_off

    def record(self, score):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.responses.append((ts, score))
        if hasattr(self, 'blink_event2'):
            self.blink_event2.cancel()
            self.ids.lamp.source = self.lamp_off

    def confirm_end(self):
        box = BoxLayout(orientation='vertical', padding=10, spacing=10)
        box.add_widget(Label(text="Zakończyć badanie?"))
        hb = BoxLayout(spacing=10, size_hint_y=None, height="40dp")
        y = Button(text="TAK"); n = Button(text="NIE")
        hb.add_widget(y); hb.add_widget(n)
        box.add_widget(hb)
        pop = Popup(title="Potwierdź", content=box,
                    size_hint=(0.8,0.4), auto_dismiss=False)
        y.bind(on_release=lambda *_: (pop.dismiss(), self.end_survey()))
        n.bind(on_release=pop.dismiss)
        pop.open()

    def end_survey(self):
        if not getattr(self, 'responses', []):
            self.manager.current = 'start'
            return
        app = App.get_running_app()
        filename = f"{self.study}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(app.log_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for t, s in self.responses:
                w.writerow([self.study, t, s])
        self.manager.current = 'start'

class LogsScreen(Screen):
    def load_logs(self):
        app = App.get_running_app()
        if not os.path.exists(app.log_dir):
            return
        files = [f for f in os.listdir(app.log_dir) if f.endswith(".csv") and "_" in f]
        self.ids.spinner.values = files
        self.ids.spinner.text = "Wybierz badanie"
        self.ids.log_box.clear_widgets()

    def show_logs(self, name):
        app = App.get_running_app()
        lb = self.ids.log_box
        lb.clear_widgets()
        filepath = os.path.join(app.log_dir, name)
        if not os.path.exists(filepath):
            return
        with open(filepath, encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) >= 3:
                    lb.add_widget(Label(text=f"{row[1]} – Ocena: {row[2]}",
                                        size_hint_y=None, height="30dp"))

class ISAApp(App):
    lamp_on = "assets/Lampka_zapalona.png"
    lamp_off = "assets/Lampka_zgaszona.png"
    log_dir = None

    def build(self):
        if platform == 'android' or platform == 'ios':
            self.log_dir = storagepath.get_documents_dir() or storagepath.get_external_storage_dir()
        else:
            self.log_dir = os.path.join(os.getcwd(), "logs")

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        return Builder.load_string(KV)

if __name__ == "__main__":
    ISAApp().run()
