from .Processor import create_dict, Processor
from .Repository import Repository
from utils import save_pkl, create_dict
import pandas as pd
import numpy as np
import os


class Splitter:
    def __init__(self, save_path: str):
        self.path = os.path.abspath(save_path)

    def set_processor(self, processor: Processor):
        self.processor = processor

    def run(self):
        parts = ["part_1_part_4", "part_3_part_4", "part_4"]
        for part in parts:
            self.split_data(part)

    def split_train_test_indexes(self, size, part="part_1_part_4"):
        indexes = np.arange(size)
        chunk_size = int(size / 5)
        part_map = {
            "part_1_part_4": {
                "start": 0,
                "end": 4,
            },
            "part_3_part_4": {
                "start": 2,
                "end": 4,
            },
            "part_4": {
                "start": 3,
                "end": 4,
            },
        }
        start = part_map[part]["start"]
        end = part_map[part]["end"]
        train_indexes = indexes[start * chunk_size : end * chunk_size]
        assert (train_indexes == np.sort(train_indexes)).all(), "Train indexes are not sorted"
        test_indexes = indexes[end * chunk_size :]
        assert (test_indexes == np.sort(test_indexes)).all(), "Test indexes are not sorted"
        return {
            "train": train_indexes,
            "test": test_indexes,
        }

    def split_train_val_indexes(self, indexes, val_train_ratio=5 / 75):
        val_indexes = np.random.choice(
            indexes["train"],
            int(len(indexes["train"]) * val_train_ratio),
            replace=False,
        )
        val_indexes = np.sort(val_indexes)
        train_indexes = np.setdiff1d(indexes["train"], val_indexes)
        assert (train_indexes == np.sort(train_indexes)).all(), "Train indexes are not sorted"
        indexes["val"] = val_indexes
        indexes["train"] = train_indexes
        return indexes

    def get_values(self, arr, indexes):
        return [arr[i] for i in indexes]

    def split_data(self, part):
        name = self.processor.repo.name
        indexes = self.split_train_test_indexes(len(self.processor.df), part)
        # split features
        for key in indexes:
            splitted_df = self.processor.df.iloc[indexes[key]]
            save_part = part if key == "train" else "part_5"
            splitted_df.to_csv(
                os.path.join(self.processor.feature_path, f"{name}_{save_part}.csv"),
                index=False,
            )
            del splitted_df
        indexes = self.split_train_val_indexes(indexes)
        # split cc2vec and deepjit codes
        for key in indexes:
            save_part = f"{name}_{part}_{key}" if key != "test" else f"{name}_part_5"
            ids = self.get_values(self.processor.ids, indexes[key])
            messages = self.get_values(self.processor.messages, indexes[key])
            cc2vec_codes = self.get_values(self.processor.cc2vec_codes, indexes[key])
            deepjit_codes = self.get_values(self.processor.deepjit_codes, indexes[key])
            simcom_codes = self.get_values(self.processor.simcom_codes, indexes[key])
            labels = self.get_values(self.processor.labels, indexes[key])
            if key == "train":
                train_dict = create_dict(messages, deepjit_codes)
                save_pkl(
                    train_dict,
                    os.path.join(
                        self.processor.commit_path, f"{save_part}_dict.pkl"
                    ),
                )
            save_pkl(
                [ids, messages, cc2vec_codes, labels],
                os.path.join(
                    self.processor.commit_path, f"cc2vec_{save_part}.pkl"
                ),
            )
            save_pkl(
                [ids, messages, deepjit_codes, labels],
                os.path.join(
                    self.processor.commit_path, f"deepjit_{save_part}.pkl"
                ),
            )
            save_pkl(
                [ids, messages, simcom_codes, labels],
                os.path.join(
                    self.processor.commit_path, f"simcom_{save_part}.pkl"
                ),
            )