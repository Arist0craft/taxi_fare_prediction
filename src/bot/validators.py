from datetime import datetime


def validate_coordinates(
    coords: tuple[str | float, str | float],
) -> tuple[float, float]:
    """Валидатор для значения координат

    Args:
        latitude (str | float): Широта
        longitude (str | float): Долгота

    Returns:
        tuple[float, float]: Кортеж с координтами в виде float значений
    """
    try:
        latitude = float(coords[0])
        longitude = float(coords[1])
    except (ValueError, TypeError):
        return

    if not (-75 <= latitude <= 65):  # Пороги взяты из EDA после очистки данных
        return

    if not (-98 <= longitude <= 41):  # Пороги взяты из EDA после очистки данных
        return

    return latitude, longitude


def validate_datetime(dt: str | datetime) -> datetime:
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except (ValueError, TypeError):
            return

    if not (2009 <= dt.year <= datetime.now().year + 5):
        return

    return dt
