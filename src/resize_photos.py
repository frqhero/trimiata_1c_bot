import os

from PIL import Image
from telegram import Update

from env_settings import settings


class DocumentResizePhotos:
    def __init__(self, src_path, dst_path):
        self.src_path = src_path
        self.dst_path = dst_path
        self.sizes = None

    def prepare_sizes_list(self):
        current_file_path = os.path.abspath(__file__)
        current_dir_path = os.path.dirname(current_file_path)
        sizes_path = os.path.join(current_dir_path, 'sizes.txt')
        with open(sizes_path, 'r') as file:
            self.sizes = [row.strip().split('x') for row in file.readlines()]

    def prepare_folders(self):
        for size in self.sizes:
            folder_name = f'{size[0]}x{size[1]}'
            folder_path = f'{self.dst_path}/{folder_name}'
            os.makedirs(folder_path, exist_ok=True)

    def resize(self):
        for root, _, files in os.walk(self.src_path):
            for file in files:
                filename, file_extension = file.split('.')
                src_file_path = f'{root}/{file}'
                for size in self.sizes:
                    folder_name = f'{size[0]}x{size[1]}'
                    folder_path = f'{self.dst_path}/{folder_name}'
                    dst_file_path = f'{folder_path}/{filename}.jpeg'
                    img = Image.open(src_file_path)
                    img = img.resize((int(size[0]), int(size[1])), Image.LANCZOS)
                    img.save(dst_file_path, 'JPEG', quality=90)


class ResizePhotos:
    media_sources_path = settings.MEDIA_SOURCES_PATH

    def __init__(self, update: Update):
        self.temp_message = update.message.reply_text('Resizing started...')
        self.src_path = os.path.join(self.media_sources_path, 'SOURCES', 'PHOTO')
        self.dst_path = os.path.join(self.media_sources_path, 'RESIZED_PHOTOS')
        self.sizes = None

    def start(self):
        try:
            document = DocumentResizePhotos(self.src_path, self.dst_path)
            document.prepare_sizes_list()
            document.prepare_folders()
            document.resize()
            self.temp_message.reply_text('Resizing completed.')
        except Exception as e:
            self.temp_message.reply_text(f'Error: {e}')
