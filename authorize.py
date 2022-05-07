import os
import json
from xml.dom import INVALID_MODIFICATION_ERR

import tweepy


class AuthorizeKeyNotFoundErrorExeption(Exception):
    def __init__(self, in_key_name) -> None:
        super().__init__(f'authorize key "{in_key_name}" is not found.')

class AuthorizeFileNotFoundError(FileNotFoundError):
    def __init__(self, in_filepath) -> None:
        super().__init__(f'authorize file "{in_filepath}" is not found.')

def authorize_from_json_file(in_filepath):
    if not os.path.isfile(in_filepath):
        raise AuthorizeFileNotFoundError(in_filepath)

    with open(in_filepath, 'r') as f:
        return authorize_from_json(json.load(f))

def authorize_from_json(in_dict):
    def get_key(in_key_name):
        if not (in_key_name in in_dict):
            raise AuthorizeKeyNotFoundErrorExeption(in_key_name)

        return in_dict[in_key_name]

    return authorize(
        get_key('api_key'),
        get_key('api_key_secret'),
        get_key('access_token'),
        get_key('access_token_secret')
    )

def authorize(in_api_key, in_api_secret, in_access_token, in_access_secret):
    auth = tweepy.OAuthHandler(in_api_key, in_api_secret)
    auth.set_access_token(in_access_token, in_access_secret)

    return auth
