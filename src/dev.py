from src.env_settings import settings

from accept_photos_new import PhotoAccept

PhotoAccept.set_source_folder(settings.PHOTO_SOURCES_PATH)


# load_dotenv()
photo_accept = PhotoAccept('PHOTO')
photo_accept.start()
1