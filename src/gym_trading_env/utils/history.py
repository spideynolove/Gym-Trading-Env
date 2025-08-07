import numpy as np
from typing import Any, Dict, List, Union, Tuple


class History:
    """
    A class to store and manage time-series history of data with fixed schema.
    Uses a NumPy array for efficient storage and supports dictionary-like access.
    """

    def __init__(self, max_size: int = 10000):
        self.height: int = max_size
        self.width: int = 0
        self.size: int = 0
        self.columns: List[str] = []
        self.history_storage: np.ndarray = np.empty((0, 0))  # Placeholder

    def set(self, **kwargs: Any) -> None:
        """
        Initialize the schema and storage based on the first input.
        Flattens lists and dictionaries into individual columns.
        """
        self.columns = []
        for name, value in kwargs.items():
            if isinstance(value, list):
                self.columns.extend([f"{name}_{i}" for i in range(len(value))])
            elif isinstance(value, dict):
                self.columns.extend([f"{name}_{key}" for key in value.keys()])
            else:
                self.columns.append(name)

        self.width = len(self.columns)
        self.history_storage = np.zeros(shape=(self.height, self.width), dtype='O')
        self.size = 0
        self.add(**kwargs)

    def add(self, **kwargs: Any) -> None:
        """
        Append a new row to the history.
        Values are flattened and aligned with the initialized column order.
        """
        values: List[Any] = []
        columns: List[str] = []

        for name, value in kwargs.items():
            if isinstance(value, list):
                columns.extend([f"{name}_{i}" for i in range(len(value))])
                values.extend(value)
            elif isinstance(value, dict):
                keys = list(value.keys())
                columns.extend([f"{name}_{k}" for k in keys])
                values.extend([value[k] for k in keys])
            else:
                columns.append(name)
                values.append(value)

        if columns != self.columns:
            raise ValueError(
                f"Column mismatch. Expected: {self.columns}. Got: {columns}"
            )

        if self.size < self.height:
            self.history_storage[self.size, :] = values
            self.size += 1
        else:
            # Overwrite oldest entry (circular buffer behavior)
            self.history_storage[:-1] = self.history_storage[1:]
            self.history_storage[-1, :] = values

    def __len__(self) -> int:
        return self.size

    def __getitem__(
        self, arg: Union[str, int, List[str], Tuple[str, Union[int, slice]]]
    ) -> Union[Any, Dict[str, Any], np.ndarray]:
        """
        Support for indexing:
            - history['column'] -> array of values
            - history['column', t] -> value at time t
            - history[t] -> dict of all columns at time t
            - history[['col1', 'col2']] -> 2D array of selected columns
        """
        data = self.history_storage[:self.size]

        if isinstance(arg, tuple):
            column, t = arg
            col_idx = self._get_column_index(column)
            return data[t, col_idx]

        elif isinstance(arg, str):
            col_idx = self._get_column_index(arg)
            return data[:, col_idx]

        elif isinstance(arg, int):
            t = arg
            return dict(zip(self.columns, data[t]))

        elif isinstance(arg, list):
            col_indices = [self._get_column_index(col) for col in arg]
            return data[:, col_indices]

        raise TypeError(f"Invalid argument type: {type(arg)}")

    def __setitem__(
        self, arg: Tuple[str, Union[int, slice]], value: Any
    ) -> None:
        """
        Support for setting values: history['column', t] = value
        """
        column, t = arg
        col_idx = self._get_column_index(column)
        self.history_storage[:self.size][t, col_idx] = value

    def _get_column_index(self, column: str) -> int:
        """Helper to get column index with error handling."""
        try:
            return self.columns.index(column)
        except ValueError:
            raise ValueError(
                f"Feature '{column}' does not exist. Available features: {self.columns}"
            )