from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd


class History:

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.columns: List[str] = []
        self.history_storage: np.ndarray = np.empty((0, 0))
        self.size: int = 0

    def set(self, **kwargs: Any) -> None:
        self.columns = self._flatten_columns(kwargs)
        self.width = len(self.columns)
        self.history_storage = np.zeros(
            shape=(self.max_size, self.width), dtype="O"
        )
        self.size = 0
        self.add(**kwargs)

    def add(self, **kwargs: Any) -> None:
        values = self._flatten_values(kwargs)
        if len(values) != self.width:
            raise ValueError(
                f"Value mismatch. Expected {self.width} values, got {len(values)}"
            )

        if self.size < self.max_size:
            self.history_storage[self.size, :] = values
            self.size += 1
        else:
            self.history_storage = np.roll(self.history_storage, -1, axis=0)
            self.history_storage[-1, :] = values

    def _flatten_columns(self, data: Dict[str, Any]) -> List[str]:
        columns = []
        for name, value in data.items():
            if isinstance(value, list):
                columns.extend([f"{name}_{i}" for i in range(len(value))])
            elif isinstance(value, dict):
                columns.extend([f"{name}_{key}" for key in value.keys()])
            else:
                columns.append(name)
        return columns

    def _flatten_values(self, data: Dict[str, Any]) -> List[Any]:
        values = []
        for value in data.values():
            if isinstance(value, (list, dict)):
                values.extend(value.values() if isinstance(value, dict) else value)
            else:
                values.append(value)
        return values

    def __len__(self) -> int:
        return self.size

    def __getitem__(
        self, arg: Union[str, int, List[str], Tuple[str, Union[int, slice]]]
    ) -> Union[Any, Dict[str, Any], np.ndarray]:
        data = self.history_storage[: self.size]
        if isinstance(arg, tuple):
            column, t = arg
            col_idx = self._get_column_index(column)
            return data[t, col_idx]
        elif isinstance(arg, str):
            col_idx = self._get_column_index(arg)
            return data[:, col_idx]
        elif isinstance(arg, int):
            return dict(zip(self.columns, data[arg]))
        elif isinstance(arg, list):
            col_indices = [self._get_column_index(col) for col in arg]
            return data[:, col_indices]
        raise TypeError(f"Invalid argument type: {type(arg)}")

    def __setitem__(self, arg: Tuple[str, Union[int, slice]], value: Any):
        column, t = arg
        col_idx = self._get_column_index(column)
        self.history_storage[t, col_idx] = value

    def _get_column_index(self, column: str) -> int:
        try:
            return self.columns.index(column)
        except ValueError:
            raise ValueError(
                f"Feature '{column}' does not exist. Available features: {self.columns}"
            )

    def to_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.history_storage[: self.size], columns=self.columns)
