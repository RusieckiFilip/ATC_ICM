import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import csv
import os
from datetime import datetime
from kivy.core.window import Window

Window.size = (360, 640)

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
            on_release: root.prompt_study_name()
        Button:
            text: "Sprawdź logi"
            size_hint_y: None
            height: "50dp"
            on_release:
                root.manager.get_screen("logs").load_logs()
                root.manager.current = "logs"
        Button:
            text: "Wyjście"
            size_hint_y: None
            height: "50dp"
            on_release: app.stop()

<SurveyScreen>:
    name: "survey"
    BoxLayout:
        orientation: "vertical"
        padding: 20
        spacing: 20
        Label:
            id: status_label
            text: "Wybierz ocenę (1–5)"
            font_size: "20sp"
        GridLayout:
            cols: 5
            spacing: 10
            size_hint_y: None
            height: "50dp"
            Button:
                text: "1"
                on_release: root.confirm_response(self.text)
            Button:
                text: "2"
                on_release: root.confirm_response(self.text)
            Button:
                text: "3"
                on_release: root.confirm_response(self.text)
            Button:
                text: "4"
                on_release: root.confirm_response(self.text)
            Button:
                text: "5"
                on_release: root.confirm_response(self.text)
        Button:
            text: "Koniec badania"
            size_hint_y: None
            height: "50dp"
            on_release: root.confirm_end_survey()  # ZMIANA

<LogsScreen>:
    name: "logs"
    BoxLayout:
        orientation: "vertical"
        padding: 10
        spacing: 10

        Spinner:
            id: session_spinner
            text: "Wybierz badanie"
            values: []
            size_hint_y: None
            height: "50dp"
            on_text: root.show_logs(self.text)

        ScrollView:
            GridLayout:
                id: logs_box
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: 5

        Button:
            text: "Powrót"
            size_hint_y: None
            height: "50dp"
            on_release: root.manager.current = "start"
'''

class StartScreen(Screen):
    def prompt_study_name(self):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        input_box = TextInput(hint_text='Wpisz nazwę badania', multiline=False)
        ok_button = Button(text="OK", size_hint_y=None, height="40dp")

        content.add_widget(input_box)
        content.add_widget(ok_button)

        popup = Popup(title="Nazwa badania", content=content,
                      size_hint=(0.8, 0.4), auto_dismiss=False)

        def on_ok(instance):
            study_name = input_box.text.strip()
            if study_name:
                self.manager.get_screen('survey').start_survey(study_name)
                popup.dismiss()
                self.manager.current = "survey"

        ok_button.bind(on_release=on_ok)
        popup.open()

class SurveyScreen(Screen):
    def start_survey(self, name):
        self.study_name = name
        self.responses = []

    def confirm_response(self, score):
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        label = Label(text=f"Zatwierdź ocenę obciążenia: {score}", size_hint_y=None, height="40dp")
        button_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height="40dp")

        # ZAMIANA ikon na TAK i NIE
        yes_button = Button(text="TAK", size_hint=(0.5, 1))
        no_button = Button(text="NIE", size_hint=(0.5, 1))

        button_box.add_widget(yes_button)
        button_box.add_widget(no_button)

        content.add_widget(label)
        content.add_widget(button_box)

        popup = Popup(title="Potwierdzenie", content=content,
                      size_hint=(0.8, 0.4), auto_dismiss=False)

        def on_yes(instance):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.responses.append((timestamp, score))
            popup.dismiss()

        def on_no(instance):
            popup.dismiss()

        yes_button.bind(on_release=on_yes)
        no_button.bind(on_release=on_no)
        popup.open()

    def confirm_end_survey(self):  # NOWA METODA
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        label = Label(text="Czy chcesz zakończyć badanie?", size_hint_y=None, height="40dp")
        button_box = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height="40dp")

        yes_button = Button(text="TAK", size_hint=(0.5, 1))
        no_button = Button(text="NIE", size_hint=(0.5, 1))

        button_box.add_widget(yes_button)
        button_box.add_widget(no_button)

        content.add_widget(label)
        content.add_widget(button_box)

        popup = Popup(title="Potwierdzenie zakończenia", content=content,
                      size_hint=(0.8, 0.4), auto_dismiss=False)

        def on_yes(instance):
            popup.dismiss()
            self.end_survey()

        def on_no(instance):
            popup.dismiss()

        yes_button.bind(on_release=on_yes)
        no_button.bind(on_release=on_no)
        popup.open()

    def end_survey(self):
        if not self.responses:
            return
        filename = f"badanie_{self.study_name}.csv"
        with open(filename, "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            for timestamp, score in self.responses:
                writer.writerow([self.study_name, timestamp, score])
        self.manager.current = "start"

class LogsScreen(Screen):
    logs_dict = {}

    def load_logs(self):
        self.logs_dict = {}
        csv_files = [f for f in os.listdir('.') if f.startswith("badanie_") and f.endswith(".csv")]

        for file in csv_files:
            name = file.replace("badanie_", "").replace(".csv", "")
            with open(file, "r", encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                self.logs_dict[name] = rows

        self.ids.session_spinner.values = list(self.logs_dict.keys())
        self.ids.session_spinner.text = "Wybierz badanie"
        self.ids.logs_box.clear_widgets()

    def show_logs(self, name):
        box = self.ids.logs_box
        box.clear_widgets()
        if name in self.logs_dict:
            for row in self.logs_dict[name]:
                if len(row) >= 3:
                    label = Label(text=f"{row[1]} - Ocena: {row[2]}", size_hint_y=None, height="30dp")
                    box.add_widget(label)

class ISAApp(App):
    def build(self):
        return Builder.load_string(KV)

if __name__ == "__main__":
    ISAApp().run()
