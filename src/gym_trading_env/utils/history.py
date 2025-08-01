import numpy as np
class History:
    def __init__(self, max_size=10000):
        self.max_size = max_size
        self.height = max_size
    def set(self, **kwargs):
        self.columns = []
        for name, value in kwargs.items():
            if isinstance(value, list):
                self.columns.extend([f'{name}_{i}' for i in range(len(value))])
            elif isinstance(value, dict):
                self.columns.extend([f'{name}_{key}' for key in value.keys()])
            else:
                self.columns.append(name)
        self.width = len(self.columns)
        self.history_storage = np.zeros(shape=(self.height, self.width),
            dtype='O')
        self.size = 0
        self.current_index = 0
        self.add(**kwargs)
    def add(self, **kwargs):
        values = []
        columns = []
        for name, value in kwargs.items():
            if isinstance(value, list):
                columns.extend([f'{name}_{i}' for i in range(len(value))])
                values.extend(value[:])
            elif isinstance(value, dict):
                columns.extend([f'{name}_{key}' for key in value.keys()])
                values.extend(list(value.values()))
            else:
                columns.append(name)
                values.append(value)
        if columns == self.columns:
            self.history_storage[self.current_index, :] = values
            self.current_index = (self.current_index + 1) % self.height
            self.size = min(self.size + 1, self.height)
        else:
            raise ValueError(
                f'Make sur that your inputs match the initial ones... Initial ones : {self.columns}. New ones {columns}'
                )
    def __len__(self):
        return self.size
    def _get_physical_index(self, logical_index):
        if self.size < self.height:
            return logical_index
        else:
            return (self.current_index + logical_index) % self.height
    def _get_ordered_data(self):
        if self.size < self.height:
            return self.history_storage[:self.size]
        else:
            start_idx = self.current_index
            return np.concatenate([self.history_storage[start_idx:], self.
                history_storage[:start_idx]])
    def __getitem__(self, arg):
        if isinstance(arg, tuple):
            column, t = arg
            try:
                column_index = self.columns.index(column)
            except ValueError as e:
                raise ValueError(
                    f'Feature {column} does not exist ... Check the available features : {self.columns}'
                    )
            if t < 0:
                t = self.size + t
            if t < 0 or t >= self.size:
                raise IndexError(
                    f'Index {t} out of range for history of size {self.size}')
            physical_index = self._get_physical_index(t)
            return self.history_storage[physical_index, column_index]
        if isinstance(arg, int):
            t = arg
            if t < 0:
                t = self.size + t
            if t < 0 or t >= self.size:
                raise IndexError(
                    f'Index {t} out of range for history of size {self.size}')
            physical_index = self._get_physical_index(t)
            return dict(zip(self.columns, self.history_storage[physical_index])
                )
        if isinstance(arg, str):
            column = arg
            try:
                column_index = self.columns.index(column)
            except ValueError as e:
                raise ValueError(
                    f'Feature {column} does not exist ... Check the available features : {self.columns}'
                    )
            return self._get_ordered_data()[:, column_index]
        if isinstance(arg, list):
            columns = arg
            column_indexes = []
            for column in columns:
                try:
                    column_indexes.append(self.columns.index(column))
                except ValueError as e:
                    raise ValueError(
                        f'Feature {column} does not exist ... Check the available features : {self.columns}'
                        )
            return self._get_ordered_data()[:, column_indexes]
    def __setitem__(self, arg, value):
        column, t = arg
        try:
            column_index = self.columns.index(column)
        except ValueError as e:
            raise ValueError(
                f'Feature {column} does not exist ... Check the available features : {self.columns}'
                )
        if t < 0:
            t = self.size + t
        if t < 0 or t >= self.size:
            raise IndexError(
                f'Index {t} out of range for history of size {self.size}')
        physical_index = self._get_physical_index(t)
        self.history_storage[physical_index, column_index] = value