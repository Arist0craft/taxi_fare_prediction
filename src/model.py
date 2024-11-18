from datetime import datetime
from pathlib import Path
from typing import Callable

import holidays
import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel, field_validator, model_validator
from pyproj import Transformer
from sklearn.base import TransformerMixin
from sklearn.pipeline import Pipeline

from src.settings import get_settings


class TaxiTravel(BaseModel):
    """
    Модель данных описывающих поездку
    """

    pickup_datetime: datetime
    pickup_latitude: float
    pickup_longitude: float
    dropoff_latitude: float
    dropoff_longitude: float
    passenger_count: float

    @field_validator("passenger_count")
    @classmethod
    def validate_passengers(cls, v: float) -> str:
        if not (1 <= v <= 8):
            raise ValueError(
                "Количество пассажиров не может быть меньше 1 и не может превышать 8"
            )

        return v

    @field_validator("pickup_latitude", "dropoff_latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> str:
        if not (-90 <= v <= 90):
            raise ValueError("Широта должна быть в пределах [-90, 90]")

        return v

    @field_validator("pickup_longitude", "dropoff_longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> str:
        if not (-180 <= v <= 180):
            raise ValueError("Долгота должна быть в пределах [-180, 180]")

        return v

    @model_validator(mode="after")
    def validate_same_coords(self) -> "TaxiTravel":
        if (
            abs(self.pickup_latitude - self.dropoff_latitude) <= 1e-5
            and abs(self.pickup_longitude - self.dropoff_longitude) <= 1e-5
        ):
            raise ValueError(
                "Точка назначения та же, что и точка отправления, измените координаты"
            )

        return self

    def model_dump_df(self) -> pd.DataFrame:
        return pd.DataFrame([self.model_dump(mode="python")])


def euclidian_distance(x1: pd.Series, x2: pd.Series, y1: pd.Series, y2: pd.Series):
    """
    Евклидово расстояние между двумя точками
    требует преобразования градусной системы координат в метрическую
    """
    return np.sqrt((y1 - x1) ** 2 + (y2 - x2) ** 2)


def calculate_distance(
    x1: pd.Series,
    x2: pd.Series,
    y1: pd.Series,
    y2: pd.Series,
    dist_func: Callable[[pd.Series, pd.Series, pd.Series, pd.Series], pd.Series],
    transformer: Transformer | None = None,
):
    if transformer:
        x1, x2 = transformer.transform(x1, x2)
        y1, y2 = transformer.transform(y1, y2)

    return dist_func(x1, x2, y1, y2)


class FeatureEngineering(TransformerMixin):
    def __init__(
        self,
        copy_x: bool = True,
        distance_func: Callable[
            [pd.Series, pd.Series, pd.Series, pd.Series], pd.Series
        ] = euclidian_distance,
    ):
        self.copy_x = copy_x
        self.distance_func = distance_func

    def fit(self, X: pd.DataFrame | None = None, y=None) -> "FeatureEngineering":
        return self

    def _add_distance(self, X: pd.DataFrame):
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857")

        x1 = X["pickup_latitude"]
        x2 = X["pickup_longitude"]
        y1 = X["dropoff_latitude"]
        y2 = X["dropoff_longitude"]

        X.loc[:, "distance_km"] = (
            calculate_distance(
                x1, x2, y1, y2, self.distance_func, transformer=transformer
            )
            / 1000
        )

        return X

    def _prepare_datetime(self, X: pd.DataFrame) -> pd.DataFrame:
        date = X["pickup_datetime"].dt.date.astype("datetime64[ns]")

        X["year"] = date.dt.year
        X["month"] = date.dt.month
        X["day"] = date.dt.day
        X["hour"] = date.dt.hour

        us_calendar = holidays.USA()

        is_holiday = date.map(us_calendar.get)
        is_holiday = is_holiday.mask(is_holiday.notna(), True)
        is_holiday = is_holiday.fillna(False)

        X["is_holiday"] = is_holiday

        X["is_weekend"] = date.dt.day_of_week > 4

        X = X.drop("pickup_datetime", axis=1)

        return X

    def transform(self, X: pd.DataFrame, y=None) -> pd.DataFrame:
        if self.copy_x:
            X = X.copy()

        X = self._add_distance(X)
        X = self._prepare_datetime(X)

        return X


def load_model(models_dir: Path) -> Pipeline:
    model_path = sorted(list(models_dir.iterdir()), reverse=True)[0]
    model = joblib.load(model_path)
    return model


settings = get_settings()

feature_transformer = FeatureEngineering()
model = load_model(settings.MODELS_DIR)


def predict(X: pd.DataFrame):
    features_order = [
        "pickup_longitude",
        "pickup_latitude",
        "dropoff_longitude",
        "dropoff_latitude",
        "passenger_count",
        "year",
        "month",
        "day",
        "hour",
        "distance_km",
        "is_holiday",
        "is_weekend",
    ]
    X = feature_transformer.transform(X)
    X = X[features_order]

    return model.predict(X)
