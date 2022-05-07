import os
import re
from datetime import datetime

import tweepy
from janome.tokenizer import Tokenizer
from nltk.lm import Vocabulary
from nltk.lm.models import MLE
from nltk.util import ngrams

from authorize import authorize_from_json_file
from config import Config
from logger import write_log
from tweet_log import TweetLog, TweetLogItem
from key_input import KeyInput 


class ApplicationModel:
    def __init__(self, in_directory: str = None) -> None:
        if in_directory is None:
            in_directory = os.getcwd()

        self.__config: Config = None
        self.__key_filepath: str = ""
        self.__tweet_log_filepath: str = ""

        self.__api: tweepy.API = None
        self.__tweet_log: TweetLog = None
        self.__tokenizer: Tokenizer = None
        self.__lm2: MLE = None
        self.__lm3: MLE = None

    def main(self) -> int:
        base_directory = os.getcwd()

        self.__config = Config()
        config_filepath = os.path.join(base_directory, "config.json")
        if os.path.isfile(config_filepath):
            self.__config.import_from_file(config_filepath)
        else:
            self.__config.export_to_file(config_filepath)

        self.__key_filepath = os.path.join(base_directory, "keys.json")
        self.__tweet_log_filepath = os.path.join(base_directory, "tweet_log.dat")

        self.__authorize()
        self.__initialize()

        write_log('次のツイートまで待機します (ESCキーで終了)')

        key_input = KeyInput()

        previous = datetime.now()
        while True:
            current = datetime.now()
            passed = current - previous

            if passed.total_seconds() > self.__config.tweet_span_in_seconds:
                text = self.__generate_new_tweet_text()

                write_log(f'新しいツイート')
                write_log(f'{text}')

                if self.__config.need_confirm_to_tweet:
                    write_log('ツイートしてもいいですか？ (y:ツイート、n:次のツイートを生成、c:キャンセル)')
                    while True:
                        response = key_input.get_key()

                        if response == b'y':
                            self.__api.update_status(text)

                            write_log('次のツイートまで待機します (ESCキーで終了)')
                            previous = current
                            break                        

                        elif response == b'n':
                            break

                        elif response == b'c':
                            write_log('次のツイートまで待機します (ESCキーで終了)')
                            previous = current
                            break
                else:
                    self.__api.update_status(text)

            if key_input.get_key() == b'\x1b':
                break

        key_input.terminate()
        write_log('終了します')

        return 0                    

    def __authorize(self):
        write_log('認証実行')

        auth = authorize_from_json_file(self.__key_filepath)
        self.__api = tweepy.API(auth, timeout=180)

    def __initialize(self):
        write_log('ログ情報初期化')

        self.__tweet_log = TweetLog()
        if os.path.isfile(self.__tweet_log_filepath):
            write_log(f'ログファイル読み込み. "{self.__tweet_log_filepath}"')
            self.__tweet_log.import_from_file(self.__tweet_log_filepath)

            if len(self.__tweet_log.items) == 0:
                write_log('ログファイル内に項目が見つかりませんでした. ツイート履歴を取得します.')
            else:
                write_log('過去の最新ツイートから現在の最新ツイートまでを取得します.')
        else:
            write_log(' ツイート履歴を取得します.')
        write_log(f'監視対象: @{self.__config.learn_target_account}')
        self.__read_to_latest()
        self.__learn()

    def __tweet_new(self) -> bool:
        text = self.__generate_new_tweet_text()

        write_log(f'新しいツイート')
        write_log(f'{text}')
        if self.__config.need_confirm_to_tweet:
            while True:
                response = input('ツイートしてもいいですか？ (y/n)').lower()
                if response == 'y':
                    self.__api.update_status(text)
                    return True
                elif response == 'n':
                    return False
        else:
            self.__api.update_status(text)

    def __learn(self):
        self.__tokenizer = Tokenizer()
        tokenizer = self.__tokenizer
        words = []
        for item in self.__tweet_log.items:
            text = item.text
            # ハッシュタグ削除
            text = re.sub(r'#.*', "", text)
            # URL削除
            text = re.sub(r'(https?)(:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)', "", text)

            w = None
            for token in tokenizer.tokenize(text):
                if w is None:
                    w = token.surface
                else:
                    w = f'{w} {token.surface}'
            words.append(w)

        words = [f'<BOP> {w} <EOP>'.split() for w in words]
        vocab = Vocabulary([item for sublist in words for item in sublist])

        bigrams = [ngrams(word, 2) for word in words]
        trigrams = [ngrams(word, 3) for word in words]

        self.__lm2 = MLE(order = 2, vocabulary=vocab)
        self.__lm2.fit(bigrams)
        self.__lm3 = MLE(order = 3, vocabulary=vocab)
        self.__lm3.fit(trigrams)

    def __generate_new_tweet_text(self):
        # ツイートを最新まで取得
        if self.__read_to_latest():
            # 再学習
            self.__learn()

        context = ['<BOP>']
        word = self.__lm2.generate(text_seed = context)
        context.append(word)
        for i in range(100):
            word = self.__lm3.generate(text_seed = context)
            if word == '<EOP>':
                break

            context.append(word)

        context = ''.join(context[1:])
        return f'{self.__config.tweet_prefix}{context}'

    def __read_to_latest(self) -> bool:
        new_items = self.__get_to_latest(self.__tweet_log.get_latest_time())
        if len(new_items) == 0:
            return False
        self.__tweet_log.items.extend(new_items)
        TweetLog.append_to_file(self.__tweet_log_filepath, new_items)
        return True

    def __get_to_latest(self, in_latest_time: datetime, in_max_count: int = -1) -> list[TweetLogItem]:
        latest_date = in_latest_time.date()
        latest_time = in_latest_time.time()

        def is_before_old_latest(in_new_time: datetime) -> bool:
            new_date = in_new_time.date()
            if new_date < latest_date:
                return True
            return (new_date == latest_date) and (in_new_time.time() <= latest_time)

        iterator = tweepy.Cursor(
                self.__api.user_timeline,
                screen_name=self.__config.learn_target_account,
                exclude_replies=True,
                include_rts=False
            )
        count = 0

        new_items = []
        for tweet in iterator.items():
            if is_before_old_latest(tweet.created_at):
                break
            print(f'\r{tweet.created_at}', end='')
            
            if tweet.text.startswith(self.__config.tweet_prefix):
                # bot自身の発言は無視
                continue

            new_items.append(TweetLogItem().import_from_status(tweet))

            count = count + 1
            if (in_max_count > 0) and (count >= in_max_count):
                break
        print(f'')

        new_items.sort(key = lambda item: item.id)            
        return new_items
