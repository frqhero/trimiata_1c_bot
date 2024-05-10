from src.env_settings import settings

from accept_photos_new import MediaAccept

MediaAccept.set_source_folder(settings.MEDIA_SOURCES_PATH)


photo_accept = MediaAccept('PHOTO')
photo_accept.start()
1
