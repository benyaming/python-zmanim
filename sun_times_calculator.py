from astronomical_calculations import AstronomicalCalculations
from datetime import date
from geo_location import GeoLocation
import math


class SunTimesCalculator(AstronomicalCalculations):
    DEG_PER_HOUR = 360.0 / 24.0

    @staticmethod
    def name():
        return 'US Naval Almanac Algorithm'

    def utc_sunrise(self, target_date: date, geo_location: GeoLocation, zenith: float, adjust_for_elevation: bool = False) -> float:
        try:
            return self.__utc_sun_position(target_date, geo_location, zenith, adjust_for_elevation, 'sunrise')
        except ValueError:
            return None

    def utc_sunset(self, target_date: date, geo_location: GeoLocation, zenith: float, adjust_for_elevation: bool = False) -> float:
        try:
            return self.__utc_sun_position(target_date, geo_location, zenith, adjust_for_elevation, 'sunset')
        except ValueError:
            return None

    def __sin_deg(self, deg: float) -> float:
        return math.sin(math.radians(deg))

    def __cos_deg(self, deg: float) -> float:
        return math.cos(math.radians(deg))

    def __tan_deg(self, deg: float) -> float:
        return math.tan(math.radians(deg))

    def __acos_deg(self, x: float) -> float:
        return math.degrees(math.acos(x))

    def __asin_deg(self, x: float) -> float:
        return math.degrees(math.asin(x))

    def __atan_deg(self, x: float) -> float:
        return math.degrees(math.atan(x))

    def __utc_sun_position(self, target_date: date, geo_location: GeoLocation, zenith: float, adjust_for_elevation: bool, mode: str) -> float:
        elevation = geo_location.elevation if adjust_for_elevation else 0
        adjusted_zenith = self.adjusted_zenith(zenith, elevation)
        utc_time = self.__calculate_utc_sun_position(target_date,
                                              geo_location.latitude,
                                              geo_location.longitude,
                                              adjusted_zenith,
                                              mode)  # in hours
        return utc_time % 24  # normalized (0...24)

    def __calculate_utc_sun_position(self, target_date: date, latitude: float, longitude: float, zenith: float, mode: str) -> float:
        day_of_year = target_date.timetuple().tm_yday
        hours_offset = self.__hours_from_meridian(longitude)
        time_days = self.__approx_time_days(day_of_year, hours_offset, mode)

        mean_anomaly = self.__sun_mean_anomaly(time_days)
        true_long = self.__sun_true_longitude(mean_anomaly)
        right_ascension_hours = self.__sun_right_ascension_hours(true_long)
        cos_local_hour_angle = self.__cos_local_hour_angle(true_long, latitude, zenith)

        local_hour_angle = self.__acos_deg(cos_local_hour_angle)
        if mode == 'sunrise':
            local_hour_angle = 360.0 - local_hour_angle

        local_hour = local_hour_angle / self.DEG_PER_HOUR

        mean_time = self.__local_mean_time(local_hour, right_ascension_hours, time_days)
        return mean_time - hours_offset

    def __local_mean_time(self, local_hour: float, right_ascension_hours: float, time_days: float) -> float:
        return local_hour + right_ascension_hours - (0.06571 * time_days) - 6.622

    def __cos_local_hour_angle(self, sun_true_long: float, latitude: float, zenith: float) -> float:
        sin_dec = 0.39782 * self.__sin_deg(sun_true_long)
        cos_dec = self.__cos_deg(self.__asin_deg(sin_dec))
        return (self.__cos_deg(zenith) - (sin_dec * self.__sin_deg(latitude))) / (cos_dec * self.__cos_deg(latitude))

    def __sun_right_ascension_hours(self, sun_true_long: float) -> float:
        ra = self.__atan_deg(0.91764 * self.__tan_deg(sun_true_long))
        l_quadrant = math.floor(sun_true_long / 90.0) * 90.0
        ra_quadrant = math.floor(ra / 90.0) * 90.0
        ra += (l_quadrant - ra_quadrant)

        return ra / self.DEG_PER_HOUR    # in hours

    def __sun_true_longitude(self, sun_mean_anomaly: float) -> float:
        true_longitude = sun_mean_anomaly + \
            (1.916 * self.__sin_deg(sun_mean_anomaly)) + \
            (0.02 * self.__sin_deg(2 * sun_mean_anomaly)) + \
            282.634
        return true_longitude % 360

    def __sun_mean_anomaly(self, time_days: float) -> float:
        return (0.9856 * time_days) - 3.289

    def __approx_time_days(self, day_of_year: int, hours_offset: float, mode: str) -> float:
        mode_offset = 6.0 if mode == 'sunrise' else 18.0
        return day_of_year + ((mode_offset - hours_offset) / 24)

    def __hours_from_meridian(self, longitude: float) -> float:
        return longitude / self.DEG_PER_HOUR
