import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
import time
from tqdm import tqdm
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup


kivy.require('2.3.0')


def download_confirm(root_popup: Popup, window: BoxLayout, confirmation: bool, version: str, url: str):
    if confirmation:
        filename = f"Shopper_{version}.apk"
        success = download(version, url)
        window.add_widget(Label(text=f"Версия {version} успешно скачана в файл {filename}.\nПуть к файлу: {os.path.abspath(filename)}"
                                if success else
                                f"Не удалось скачать версию {version}: Неполные данные"))
    else:
        window.add_widget(Label(text="Выбор не сделан."))
    root_popup.dismiss()


class Main(App):
    def build(self):
        self.window = BoxLayout(padding=10, orientation="vertical")
        self.button_box = BoxLayout(padding=10, orientation="vertical")

        self.local_timezone = pytz.FixedOffset(time.timezone//60)

        self.load_url = 'https://storage.yandexcloud.net/sbermarker-shopper-distribution/'
        self.response = requests.get(self.load_url)

        self.root_xml = ET.fromstring(self.response.content)
        self.namespace = {'ns': 'http://s3.amazonaws.com/doc/2006-03-01/'}

        self.versions = []

        for content in self.root_xml.findall('ns:Contents', self.namespace):
            key = content.find('ns:Key', self.namespace).text
            version = key.split('/')[-1].replace('shopper-', '').replace('.apk', '')
            self.versions.append(version)

        self.show_versions()

        return self.window

    def show_versions(self):
        self.window.add_widget(Label(text="Доступные версии:"))
        for i, version in enumerate(reversed(self.versions)):
            butt = Button(text=f"{i + 1}. Версия {version}")
            butt.bind(on_press=lambda a: self.load_version(i))
            self.window.add_widget(butt)

    def load_version(self, choice: int):
        self.window.clear_widgets()
        self.show_versions()
        chosen_version = self.versions[-choice]

        if self.response.status_code != 200:
            self.window.add_widget(Label(text=f"Не удалось получить XML: {self.response.status_code}"))
            return
        for content in self.root_xml.findall('ns:Contents', self.namespace):
            key = content.find('ns:Key', self.namespace).text
            version = key.split('/')[-1].replace('shopper-', '').replace('.apk', '')
            if version == chosen_version:
                last_modified_utc = content.find('ns:LastModified', self.namespace).text
                size_bytes = int(content.find('ns:Size', self.namespace).text)

                last_modified_dt = datetime.fromisoformat(last_modified_utc.replace('Z', '+00:00'))
                local_time = last_modified_dt.astimezone(self.local_timezone)
                local_time_str = local_time.strftime('%d.%m.%y %H:%M:%S')
                received_time_str = last_modified_dt.strftime('%H:%M:%S')

                size_mb = round(size_bytes / 0x100000, 1)

                download_url = self.load_url + key

                self.window.add_widget(Label())
                self.window.add_widget(Label(text=f"Вы выбрали скачивание Версии {chosen_version}:"))
                self.window.add_widget(Label(text="Размер:"))
                self.window.add_widget(Label(text=f"{size_mb} МБ"))
                self.window.add_widget(Label())
                self.window.add_widget(Label(text="Ссылка для скачивания"))
                self.window.add_widget(Label(text=f"{download_url}"))
                self.window.add_widget(Label())
                self.window.add_widget(Label(text="Последнее изменение:"))
                self.window.add_widget(Label(text=f"{local_time_str} (локальное время: {received_time_str}, часовой пояс: {self.local_timezone})"))
                self.window.add_widget(Label())

                popup_content = BoxLayout(padding=10, spacing=10, orientation="vertical")

                popup_content.add_widget(Label(text="Желаете скачать выбранную версию?"))

                popup_buttons = BoxLayout(padding=10, spacing=10, orientation="horizontal")
                button_yes = Button(text="Да")
                button_no = Button(text="Нет")
                popup_content.add_widget(button_yes)
                popup_content.add_widget(button_no)
                popup_content.add_widget(popup_buttons)

                popup = Popup(title="Подтвердите", content=popup_content, size_hint=(None, None), size=(400, 200))

                button_yes.bind(on_press=lambda a: download_confirm(popup, self.window, True, chosen_version, download_url))
                button_no.bind(on_press=lambda a: download_confirm(popup, self.window, False, chosen_version, download_url))

                popup.open()

                break


def download(version: str, url: str) -> bool:
    filename = f"Shopper_{version}.apk"
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        with open(filename, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Скачивание версии {version}", leave=False) as pbar:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        downloaded_size = os.path.getsize(filename)
        return total_size == downloaded_size


if __name__ == "__main__":
    Main().run()
    # main()
