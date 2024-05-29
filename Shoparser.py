import os
import requests
import xml.etree.ElementTree as ET
import click
from datetime import datetime
import pytz
import tzlocal
from tqdm import tqdm

@click.command()
def main():
    local_timezone = tzlocal.get_localzone()

    url = 'https://storage.yandexcloud.net/sbermarker-shopper-distribution/'
    response = requests.get(url)

    if response.status_code == 200:
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://s3.amazonaws.com/doc/2006-03-01/'}
        
        versions = []
        
        for content in root.findall('ns:Contents', namespace):
            key = content.find('ns:Key', namespace).text
            version = key.split('/')[-1].replace('shopper-', '').replace('.apk', '')
            versions.append(version)
        
        click.echo("Доступные версии:")
        for i, version in enumerate(versions):
            click.echo(f"{i + 1}. Версия {version}")

        choice = click.prompt("Выберите версию для скачивания", type=int, default=1, show_default=True)

        chosen_version = versions[choice - 1]

        for content in root.findall('ns:Contents', namespace):
            key = content.find('ns:Key', namespace).text
            version = key.split('/')[-1].replace('shopper-', '').replace('.apk', '')
            if version == chosen_version:
                last_modified_utc = content.find('ns:LastModified', namespace).text
                size_bytes = int(content.find('ns:Size', namespace).text)

                last_modified_dt = datetime.fromisoformat(last_modified_utc.replace('Z', '+00:00'))
                local_time = last_modified_dt.astimezone(local_timezone)
                local_time_str = local_time.strftime('%d.%m.%y %H:%M:%S')
                received_time_str = last_modified_dt.strftime('%H:%M:%S')

                size_mb = round(size_bytes / (1024 * 1024), 1)

                download_url = url + key

                click.echo(f"Вы выбрали скачивание Версии {chosen_version}:")
                click.echo(f"- Последнее изменение: {local_time_str} (локальное время: {received_time_str}, часовой пояс: {local_timezone})")
                click.echo(f"- Размер: {size_mb} МБ")
                click.echo(f"- Ссылка для скачивания: {download_url}")
                
                download_choice = click.confirm("Желаете скачать выбранную версию?", default=True)
                
                if download_choice:
                    download(chosen_version, download_url)
                else:
                    click.echo("Выбор не сделан.")
                
                break
    else:
        click.echo(f"Не удалось получить XML: {response.status_code}")

def download(version, url):
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
        if total_size == downloaded_size:
            click.echo(f"Версия {version} успешно скачана в файл {filename}.")
            click.echo(f"Путь к файлу: {os.path.abspath(filename)}")
        else:
            click.echo(f"Не удалось скачать версию {version}: Неполные данные")

if __name__ == "__main__":
    main()
