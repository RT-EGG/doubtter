from msilib.schema import Binary
from operator import le
import os
import tweepy
from datetime import datetime, tzinfo
from parse import parse


class TweetLogItem:
    def __init__(self) -> None:
        self.time: datetime = None
        self.id: int = None
        self.text: str = ""

    def export_to_binary(self) -> bytearray:
        time = bytearray(self.datetime_to_str(self.time), 'utf-8')
        id = self.id.to_bytes(8, 'little')
        text = bytearray(self.text, 'utf-8')
        
        return b''.join([
            len(time).to_bytes(4, 'little'), time,
            len(id).to_bytes(4, 'little'), id,
            len(text).to_bytes(4, 'little'), text
        ])

    def import_from_binary(self, in_data: bytearray):
        index = 0

        length = int.from_bytes(in_data[index:index+4], 'little')
        index = index + 4
        self.time = self.str_to_datetime(in_data[index:index+length].decode('utf-8'))
        index = index + length

        length = int.from_bytes(in_data[index:index+4], 'little')
        index = index + 4
        self.id = int.from_bytes(in_data[index:index+length], 'little')
        index = index + length

        length = int.from_bytes(in_data[index:index+4], 'little')
        index = index + 4
        self.text = in_data[index:index+length].decode('utf-8')

        return self

    def import_from_status(self, in_status):
        self.time = in_status.created_at
        self.id = in_status.id
        self.text = in_status.text
        return self

    @staticmethod
    def datetime_to_str(in_datetime):
        return f'{in_datetime.year}-{in_datetime.month}-{in_datetime.day} {in_datetime.hour}:{in_datetime.minute}:{in_datetime.second}'

    @staticmethod
    def str_to_datetime(in_str):
        year, month, day, hour, minute, second = parse('{}-{}-{} {}:{}:{}', in_str)
        return datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))


class TweetLog:    
    def __init__(self) -> None:
        self.items: list[TweetLogItem] = []

    def export_to_file(self, in_filepath):
        os.makedirs(os.path.dirname(in_filepath), exist_ok=True)

        with open(in_filepath, 'wb') as f:
            for item in self.items:
                binary = item.export_to_binary()
                f.write(len(binary).to_bytes(4, 'little'))
                f.write(binary)

    def import_from_file(self, in_filepath):
        if not os.path.isfile(in_filepath):
            raise FileNotFoundError(f'"{in_filepath}" is not found.')
        
        self.items = []
        with open(in_filepath, 'rb') as f:
            while True:
                size = f.read(4)
                if len(size) == 0:
                    break

                size = int.from_bytes(size, 'little')
                data = f.read(size)

                try:
                    self.items.append(TweetLogItem().import_from_binary(data))

                except:
                    continue

    def get_latest_time(self) -> datetime:
        if len(self.items) == 0:
            return datetime(1990, 1, 1)
        else:
            return self.items[-1].time
    
    @staticmethod
    def append_to_file(in_filepath: str, in_items: list[TweetLogItem]):
        mode = 'ab'
        if not os.path.isfile(in_filepath):
            os.makedirs(os.path.dirname(in_filepath), exist_ok=True)
            mode = 'wb'

        with open(in_filepath, mode) as f:
            for item in in_items:
                binary = item.export_to_binary()
                f.write(len(binary).to_bytes(4, 'little'))
                f.write(binary)

