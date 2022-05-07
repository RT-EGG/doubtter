import os
import json
from typing import Any

class Config:
    def __init__(self) -> None:
        self.learn_target_account: str = ''
        self.tweet_prefix: str = '[bot]'
        self.need_confirm_to_tweet: bool = True
        self.tweet_span_in_seconds: int = 60

    def import_from_json(self, in_dict: dict) -> None:
        def get_or_def(in_key: str, in_def: Any) -> Any:
            if in_key in in_dict:
                return in_dict[in_key]
            return in_def

        self.learn_target_account = get_or_def('learn_target_account', '')
        self.tweet_prefix = get_or_def('tweet_prefix', '[bot]')
        self.need_confirm_to_tweet = get_or_def('need_confirm_to_tweet', True)
        self.tweet_span_in_seconds = get_or_def('tweet_span_in_seconds', 60)

    def import_from_file(self, in_filepath: str) -> None:
        if not os.path.isfile(in_filepath):
            raise FileNotFoundError(in_filepath)

        with open(in_filepath, 'r') as f:
            self.import_from_json(json.load(f))

    def export_to_json(self) -> dict:
        return {
            'learn_target_account': self.learn_target_account,
            'tweet_prefix': self.tweet_prefix,
            'need_confirm_to_tweet': self.need_confirm_to_tweet,
            'tweet_span_in_seconds': self.tweet_span_in_seconds
        }

    def export_to_file(self, in_filepath: str) -> None:
        os.makedirs(os.path.dirname(in_filepath), exist_ok=True)

        with open(in_filepath, 'w') as f:
            json.dump(self.export_to_json(), f, indent=4)
