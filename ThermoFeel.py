# (C) Copyright 1996- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""
  Thermofeel is a library that contains all the methods to calculate different heat indices.
  Relative Humidity Percentage, Relative Humidity [pa],Heat Index,Solar Zenith Angle, Mean Radiant Temperature,
  Universal Thermal Climate Index,Wet Bulb Globe Temperature Simple,Wet Bulb Globe Temperature,
  Mean Radiant Temperature from Wet Bulb Globe Temperature, Humidex, Net Effective Temperature,
  Apparent Temperature and Wind Chill
  """

import numpy as np
import math
import datetime

from math import cos, sin


to_radians = np.pi / 180


def __julian_date(d, m, y):
    return d - 32075 + 1461 * (y + 4800 + (m - 14) / 12) / 4 + 367 * (m - 2 - (m - 14) / 12 * 12) / 12 - 3 * (
        (y + 4900 + (m - 14) / 12) / 100) / 4


# solar declination angle [degrees] + time correction for solar angle
def __declination_angle(jd, h):
    g = (360 / 365.25) * (jd + (h / 24))  # fractional year g in degrees
    while (g > 360):
        g = g - 360
    grad = g * to_radians
    # declination in [degrees]
    d = 0.396372 - 22.91327 * np.cos(grad) + 4.02543 * np.sin(grad) - 0.387205 * np.cos(2 * grad) + 0.051967 * np.sin(
        2 * grad) - 0.154527 * np.cos(3 * grad) + 0.084798 * np.sin(3 * grad)
    # time correction in [ h.degrees ]
    tc = 0.004297 + 0.107029 * np.cos(grad) - 1.837877 * np.sin(grad) \
        - 0.837378 * np.cos(2 * grad) - 2.340475 * np.sin(2 * grad)
    return d, tc


# calculate wind speed from components
def __calculate_wind_speed(u, v):
    ws = np.sqrt(u ** 2 + v ** 2)
    return ws


# validate data convert int float to numpy array
def __wrap(variable):
    if isinstance(variable, int) or isinstance(variable, float):
        variable = np.array(variable)
        return variable
    if variable is None:
        raise ValueError
    else:
        return variable


# convert farenheit to kelvin
def __farenheit_to_kelvin(t2m):
    t2m = (t2m + 459.67) * 5 / 9
    return t2m


# convert kelvin to celcius
def __kelvin_to_celcius(t2m):
    t2m = np.subtract(t2m, 273.15)
    return t2m


# convert celcius to kelvin
def __celcius_to_kelvin(t2m):
    t2m = t2m + 273.15
    return t2m


# convert from pa to hpa for e (relative humidity)
def __pa_to_hpa(rh):
    rh = rh / 10
    return rh


def calculate_relative_humidity_percent(t2m, td):
    """Relative Humidity in percent
        :param t2m: (float array) 2m temperature [K]
        :param td: (float array) dew point temperature [K]

        returns relative humidity [%]
        """
    t2m = __wrap(t2m)
    td = __wrap(td)

    es = 6.11 * 10.0 ** (7.5 * t2m / (237.7 + t2m))
    e = 6.11 * 10.0 ** (7.5 * td / (237.7 + td))
    rh = (e / es) * 100
    return rh


def calculate_relative_humidity(t2m):
    """Relative Humidity
        :param t2m: (float array) 2m temperature [K]
         returns relative humidity [pa]
    """
    t2m = __wrap(t2m)
    t2m = __kelvin_to_celcius(t2m)
    t2m = __kelvin_to_celcius(t2m)
    g = [-2.8365744e3, -6.028076559e3, 1.954263612e1, -2.737830188e-2,
         1.6261698e-5, 7.0229056e-10, -1.8680009e-13, 2.7150305]
    tk = t2m + 273.15
    ess = g[7] * np.log(tk)
    for i in range(7):
        ess = ess + g[i] * pow(tk, (i - 2))
    ess = np.exp(ess) * 0.01
    return ess


def calculate_heat_index(t2m, rh=None):
    """
    Heat Index
       :param t2m: np.array 2m temperature [K]
       :param rh: Relative Humidity [pa]
       returns heat index [°C]
       """
    t2m = __wrap(t2m)
    if rh is None:
        rh = calculate_relative_humidity(t2m)
    t2m = __kelvin_to_celcius(t2m)
    rh = __pa_to_hpa(rh)
    hiarray = [8.784695, 1.61139411, 2.338549, 0.14611605, 1.2308094E-2, 2.211732E-3,
               7.2546E-4, 3.58E-6]
    hi = -hiarray[0] + hiarray[1] * t2m + hiarray[2] * rh - hiarray[3] * t2m * \
         rh - hiarray[4] * rh ** 2 + hiarray[5] * t2m ** 2 * rh + hiarray[6] * \
         t2m * rh ** 2 - hiarray[7] * t2m ** 2 * rh ** 2
    return hi


def calculate_cos_solar_zenith_angle(lat, lon, y, m, d, h):
    """
    calculate solar zenith angle
    :param lat: (float array) latitude [degrees]
    :param lon: (float array) longitude [degrees]
    :param y: year [int]
    :param m: month [int]
    :param d: day [int]
    :param h: hour [int]

    https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1002/2015GL066868
    
    see also:
    http://answers.google.com/answers/threadview/id/782886.html

    returns cosine of the solar zenith angle
    """

    # convert to julian days counting from the beginning of the year
    jd_ = __julian_date(d, m, y)  # julian date of data
    jd11_ = __julian_date(1, 1, y)  # julian date 1st Jan
    jd = jd_ - jd11_ + 1  # days since start of year

    # declination angle + time correction for solar angle
    d, tc = __declination_angle(jd, h)
    drad = d * to_radians

    latrad = lat * to_radians

    sindec_sinlat = np.sin(drad) * np.sin(latrad)
    cosdec_coslat = np.cos(drad) * np.cos(latrad)

    # solar hour angle [h.deg]
    sharad = ((h - 12) * 15 + lon + tc) * to_radians
    csza = sindec_sinlat + cosdec_coslat * np.cos(sharad)
    return np.clip(csza, 0, None)


def calculate_cos_solar_zenith_angle_integrated(lat, lon, y, m, d, h, base, step):
        """
        calculate solar zenith angle
        :param lat: (int array) latitude [degrees]
        :param lon: (int array) longitude [degrees]
        :param y: year [int]
        :param m: month [int]
        :param d: day [int]
        :param h: hour [int]
        :param base: base time of forecast enum [0,6,18,12]
        :param step: step interval of forecast enum [1,3,6]

        https://agupubs.onlinelibrary.wiley.com/doi/epdf/10.1002/2015GL066868

        returns cosine of the solar zenith angle [degrees]
        """

        maxx = 0
        base_offset = 0
        h_offset = 0
        step_offset = 0
        if base == 0:
            base_offset = 0
        if base == 6:
            base_offset = 594
        if base == 18:
            base_offset = 1806
        if base == 12:
            base_offset = 1212 # 1200+12

        if step == 1:
            h_offset = 0.5
            maxx = 32.0
        if step == 3:
            h_offset = 1.5
            maxx = 14.0
        if step == 6:
            h_offset = 3
            maxx = 100.0

        hh = h - base_offset - h_offset

        ### POTENTIAL BUG -- POSSIBLE FIX ????
        ### This ensures we can integrate but doesn't use hours offsets
        hh = h
        maxx = 100.0

        # convert to julian days counting from the beginning of the year
        jd_ = __julian_date(d, m, y)  # julian date of data
        jd11_ = __julian_date(1, 1, y)  # julian date 1st Jan
        jd = jd_ - jd11_ + 1  # days since start of year

        # declination angle + time correction for solar angle
        d, tc = __declination_angle(jd, hh)
        drad = d * to_radians

        # solar hour angle
        sha = (hh - 12) * 15 + (lon + 180) / 2 + tc # solar hour angle
        latrad = lat * to_radians
        lonrad = (lon + 180) / 2 * to_radians
        accumulationperiod = step # hours
        # 2*3.1415=day in rad; /24=day hour in rad; *accumulationperiod/2; = half of the (radiation) accumulation period - SUN IN THE MIDDLE!
        zhalftimestep = (2 * np.pi) / 24 * accumulationperiod / 2
        zsolartimestart = sha * np.pi / 180 - zhalftimestep
        zsolartimeend = sha * np.pi / 180 + zhalftimestep
        ztandec = sin(d * np.pi / 180) / max((cos(d * np.pi / 180), 1.0e-12))
        zcoshouranglesunset = -ztandec * np.sin(latrad) / np.clip(np.cos(latrad), 1.0e-12, None) 
        zsindecsinlat = sin(d * np.pi / 180) * np.sin(latrad)
        zcosdeccoslat = cos(d * np.pi / 180) * np.cos(latrad)        

        def solar_zenith_angle_average(lonrad, zcoshouranglesunset, zsindecsinlat, zcosdeccoslat, zsolartimestart, zsolartimeend, sha):
            # start and end hour
            def horizon(val, rrange, lonrad, zsolartimestart, zsolartimeend, maxx):
                if (val < rrange * math.pi):
                    zhouranglestart = zsolartimestart + lonrad - ((rrange - 1.0) * math.pi)
                    zhourangleend = zsolartimeend + lonrad - ((rrange - 1.0) * math.pi)
                else:
                    if rrange < maxx:
                        zhouranglestart, zhourangleend = \
                        horizon(val, rrange + 2.0, lonrad, zsolartimestart, zsolartimeend, maxx)
                    else:
                        zhouranglestart = zsolartimestart + lonrad - (maxx + 1.0) * math.pi
                        zhourangleend = zsolartimeend + lonrad - (maxx + 1.0) * math.pi

                return (zhouranglestart, zhourangleend)

            # calculating the solar zenith angle
            
            PMU0 = 0    
            if zcoshouranglesunset <= 1:
                zhouranglestart, zhourangleend = \
                    horizon(sha * math.pi / 180 + lonrad, 2, lonrad, zsolartimestart, zsolartimeend, maxx)

                if zcoshouranglesunset >= -1:
                    zhouranglesunset = math.acos(zcoshouranglesunset)
                    if zhourangleend <= -zhouranglesunset or zhouranglestart >= zhouranglesunset:
                        PMU0 = 0
                    zhouranglestart = max(-zhouranglesunset, min(zhouranglestart, zhouranglesunset))
                    zhourangleend = max(-zhouranglesunset, min(zhourangleend, zhouranglesunset))

                if (zhourangleend - zhouranglestart) > 1.0e-8:
                    PMU0 = max(0.0, zsindecsinlat + (zcosdeccoslat * (sin(zhourangleend) - sin(zhouranglestart))) / (zhourangleend - zhouranglestart))
                else:
                    PMU0 = 0.0

            return PMU0
        
        return np.vectorize(solar_zenith_angle_average)(lonrad, zcoshouranglesunset, zsindecsinlat, zcosdeccoslat, zsolartimestart, zsolartimeend, sha)


def calculate_mean_radiant_temperature(ssrd, ssr, fdir, strd, strr, cossza):
    """
            mrt - Mean Radiant Temperature
            :param ssrd: is surface solar radiation downwards [J/m^-2]
            :param ssr: is surface net solar radiation [J/m^-2]
            :param fdir: is Total sky direct solar radiation at surface [J/m^-2]
            :param strd: is Surface thermal radiation downwards [J/m^-2]
            :param strr: is Surface net thermal radiation [J/m^-2]
            :param cossza: is cosine of solar zenith angle [degrees]

            returns Mean Radiant Temperature [K]
           """
    dsw = ssrd - fdir
    rsw = ssrd - ssr
    lur = strd - strr


    # calculate fp projected factor area
    gamma = np.arcsin(cossza) * 180 / np.pi
    fp = 0.308 * np.cos(np.pi / 180) * gamma * 0.998 - gamma * gamma / 50000

    #filter statement for solar zenith angle
    csza_filter1 = np.where((cossza > 0.01))
    fdir[csza_filter1] = fdir[csza_filter1]/cossza[csza_filter1]

    # calculate mean radiant temperature
    mrtcal = np.power(((1/0.0000000567) * (0.5 * strd + 0.5 * lur + (0.7 / 0.97) * (0.5 * dsw + 0.5 * rsw + fp * fdir))),0.25)

    mrt = mrtcal
    mrt = __kelvin_to_celcius(mrt)
    return mrt


def calculate_utci(t2m, va, mrt, rh=None):
    """
        UTCI
        :param t: (float array) is 2m temperature [K]
        :param va: (float array) is wind speed at 10 meters [m/s]
        :param mrt:(float array) is mean radiant temperature [K]
        :param rh: (float array) is relative humidity [pa]

        Calculate UTCI with a 6th order polynomial approximation according to:
        Brode, P. et al. Deriving the operational procedure for the
        Universal Thermal Climate Index (UTCI). Int J Biometeorol (2012) 56: 48.1

        returns UTCI [°C]

        """
    t2m = __wrap(t2m)
    va = __wrap(va)
    mrt = __wrap(mrt)

    mrt = __kelvin_to_celcius(mrt)

    if rh is None:
        rh = calculate_relative_humidity(t2m)

    t2m = __kelvin_to_celcius(t2m)
    e_mrt = np.subtract(mrt, t2m)
    rh = rh / 10.0

    t2m2 = t2m * t2m
    t2m3 = t2m2 * t2m
    t2m4 = t2m3 * t2m
    t2m5 = t2m4 * t2m
    t2m6 = t2m5 * t2m

    va2 = va * va
    va3 = va2 * va
    va4 = va3 * va
    va5 = va4 * va
    va6 = va5 * va

    e_mrt2 = e_mrt * e_mrt
    e_mrt3 = e_mrt2 * e_mrt
    e_mrt4 = e_mrt3 * e_mrt
    e_mrt5 = e_mrt4 * e_mrt
    e_mrt6 = e_mrt5 * e_mrt

    rh2 = rh * rh
    rh3 = rh2 * rh
    rh4 = rh3 * rh
    rh5 = rh4 * rh
    rh6 = rh5 * rh

    utci_approx = t2m + 6.07562052E-01 + \
                  -2.27712343E-02 * t2m + \
                  8.06470249E-04 * t2m2 + \
                  -1.54271372E-04 * t2m3 + \
                  -3.24651735E-06 * t2m4 + \
                  7.32602852E-08 * t2m5 + \
                  1.35959073E-09 * t2m6 + \
                  -2.25836520E+00 * va + \
                  8.80326035E-02 * t2m * va + \
                  2.16844454E-03 * t2m2 * va + \
                  -1.53347087E-05 * t2m3 * va + \
                  -5.72983704E-07 * t2m4 * va + \
                  -2.55090145E-09 * t2m5 * va + \
                  -7.51269505E-01 * va2 + \
                  -4.08350271E-03 * t2m * va2 + \
                  -5.21670675E-05 * t2m2 * va2 + \
                  1.94544667E-06 * t2m3 * va2 + \
                  1.14099531E-08 * t2m4 * va2 + \
                  1.58137256E-01 * va3 + \
                  -6.57263143E-05 * t2m * va3 + \
                  2.22697524E-07 * t2m2 * va3 + \
                  -4.16117031E-08 * t2m3 * va3 + \
                  -1.27762753E-02 * va4 + \
                  9.66891875E-06 * t2m * va4 + \
                  2.52785852E-09 * t2m2 * va4 + \
                  4.56306672E-04 * va5 + \
                  -1.74202546E-07 * t2m * va5 + \
                  -5.91491269E-06 * va6 + \
                  3.98374029E-01 * e_mrt + \
                  1.83945314E-04 * t2m * e_mrt + \
                  -1.73754510E-04 * t2m2 * e_mrt + \
                  -7.60781159E-07 * t2m3 * e_mrt + \
                  3.77830287E-08 * t2m4 * e_mrt + \
                  5.43079673E-10 * t2m5 * e_mrt + \
                  -2.00518269E-02 * va * e_mrt + \
                  8.92859837E-04 * t2m * va * e_mrt + \
                  3.45433048E-06 * t2m2 * va * e_mrt + \
                  -3.77925774E-07 * t2m3 * va * e_mrt + \
                  -1.69699377E-09 * t2m4 * va * e_mrt + \
                  1.69992415E-04 * va2 * e_mrt + \
                  -4.99204314E-05 * t2m * va2 * e_mrt + \
                  2.47417178E-07 * t2m2 * va2 * e_mrt + \
                  1.07596466E-08 * t2m3 * va2 * e_mrt + \
                  8.49242932E-05 * va3 * e_mrt + \
                  1.35191328E-06 * t2m * va3 * e_mrt + \
                  -6.21531254E-09 * t2m2 * va3 * e_mrt + \
                  -4.99410301E-06 * va4 * e_mrt + \
                  -1.89489258E-08 * t2m * va4 * e_mrt + \
                  8.15300114E-08 * va5 * e_mrt + \
                  7.55043090E-04 * e_mrt2 + \
                  -5.65095215E-05 * t2m * e_mrt2 + \
                  -4.52166564E-07 * t2m * e_mrt2 + \
                  2.46688878E-08 * t2m3 * e_mrt2 + \
                  2.42674348E-10 * t2m4 * e_mrt2 + \
                  1.54547250E-04 * va * e_mrt2 + \
                  5.24110970E-06 * t2m * va * e_mrt2 + \
                  -8.75874982E-08 * t2m2 * va * e_mrt2 + \
                  -1.50743064E-09 * t2m3 * va * e_mrt2 + \
                  -1.56236307E-05 * va2 * e_mrt2 + \
                  -1.33895614E-07 * t2m * va2 * e_mrt2 + \
                  2.49709824E-09 * t2m2 * va2 * e_mrt2 + \
                  6.51711721E-07 * va3 * e_mrt2 + \
                  1.94960053E-09 * t2m * va3 * e_mrt2 + \
                  -1.00361113E-08 * va4 * e_mrt2 + \
                  -1.21206673E-05 * e_mrt3 + \
                  -2.18203660E-07 * t2m * e_mrt3 + \
                  7.51269482E-09 * t2m2 * e_mrt3 + \
                  9.79063848E-11 * t2m3 * e_mrt3 + \
                  1.25006734E-06 * va * e_mrt3 + \
                  -1.81584736E-09 * t2m * va * e_mrt3 + \
                  -3.52197671E-10 * t2m2 * va * e_mrt3 + \
                  -3.36514630E-08 * va2 * e_mrt3 + \
                  1.35908359E-10 * t2m * va2 * e_mrt3 + \
                  4.17032620E-10 * va3 * e_mrt3 + \
                  -1.30369025E-09 * e_mrt4 + \
                  4.13908461E-10 * t2m * e_mrt4 + \
                  9.22652254E-12 * t2m2 * e_mrt4 + \
                  -5.08220384E-09 * va * e_mrt4 + \
                  -2.24730961E-11 * t2m * va * e_mrt4 + \
                  1.17139133E-10 * va2 * e_mrt4 + \
                  6.62154879E-10 * e_mrt5 + \
                  4.03863260E-13 * t2m * e_mrt5 + \
                  1.95087203E-12 * va * e_mrt5 + \
                  -4.73602469E-12 * e_mrt6 + \
                  5.12733497E+00 * rh + \
                  -3.12788561E-01 * t2m * rh + \
                  -1.96701861E-02 * t2m2 * rh + \
                  9.99690870E-04 * t2m3 * rh + \
                  9.51738512E-06 * t2m4 * rh + \
                  -4.66426341E-07 * t2m5 * rh + \
                  5.48050612E-01 * va * rh + \
                  -3.30552823E-03 * t2m * va * rh + \
                  -1.64119440E-03 * t2m2 * va * rh + \
                  -5.16670694E-06 * t2m3 * va * rh + \
                  9.52692432E-07 * t2m4 * va * rh + \
                  -4.29223622E-02 * va2 * rh + \
                  5.00845667E-03 * t2m * va2 * rh + \
                  1.00601257E-06 * t2m2 * va2 * rh + \
                  -1.81748644E-06 * t2m3 * va2 * rh + \
                  -1.25813502E-03 * va3 * rh + \
                  -1.79330391E-04 * t2m * va3 * rh + \
                  2.34994441E-06 * t2m2 * va3 * rh + \
                  1.29735808E-04 * va4 * rh + \
                  1.29064870E-06 * t2m * va4 * rh + \
                  -2.28558686E-06 * va5 * rh + \
                  -3.69476348E-02 * e_mrt * rh + \
                  1.62325322E-03 * t2m * e_mrt * rh + \
                  -3.14279680E-05 * t2m2 * e_mrt * rh + \
                  2.59835559E-06 * t2m3 * e_mrt * rh + \
                  -4.77136523E-08 * t2m4 * e_mrt * rh + \
                  8.64203390E-03 * va * e_mrt * rh + \
                  -6.87405181E-04 * t2m * va * e_mrt * rh + \
                  -9.13863872E-06 * t2m2 * va * e_mrt * rh + \
                  5.15916806E-07 * t2m3 * va * e_mrt * rh + \
                  -3.59217476E-05 * va2 * e_mrt * rh + \
                  3.28696511E-05 * t2m * va2 * e_mrt * rh + \
                  -7.10542454E-07 * t2m2 * va2 * e_mrt * rh + \
                  -1.24382300E-05 * va3 * e_mrt * rh + \
                  -7.38584400E-09 * t2m * va3 * e_mrt * rh + \
                  2.20609296E-07 * va4 * e_mrt * rh + \
                  -7.32469180E-04 * e_mrt2 * rh + \
                  -1.87381964E-05 * t2m * e_mrt2 * rh + \
                  4.80925239E-06 * t2m2 * e_mrt2 * rh + \
                  -8.75492040E-08 * t2m3 * e_mrt2 * rh + \
                  2.77862930E-05 * va * e_mrt2 * rh + \
                  -5.06004592E-06 * t2m * va * e_mrt2 * rh + \
                  1.14325367E-07 * t2m2 * va * e_mrt2 * rh + \
                  2.53016723E-06 * va2 * e_mrt2 * rh + \
                  -1.72857035E-08 * t2m * va2 * e_mrt2 * rh + \
                  -3.95079398E-08 * va3 * e_mrt2 * rh + \
                  -3.59413173E-07 * e_mrt3 * rh + \
                  7.04388046E-07 * t2m * e_mrt3 * rh + \
                  -1.89309167E-08 * t2m2 * e_mrt3 * rh + \
                  -4.79768731E-07 * va * e_mrt3 * rh + \
                  7.96079978E-09 * t2m * va * e_mrt3 * rh + \
                  1.62897058E-09 * va2 * e_mrt3 * rh + \
                  3.94367674E-08 * e_mrt4 * rh + \
                  -1.18566247E-09 * t2m * e_mrt4 * rh + \
                  3.34678041E-10 * va * e_mrt4 * rh + \
                  -1.15606447E-10 * e_mrt5 * rh + \
                  -2.80626406E+00 * rh2 + \
                  5.48712484E-01 * t2m * rh2 + \
                  -3.99428410E-03 * t2m2 * rh2 + \
                  -9.54009191E-04 * t2m3 * rh2 + \
                  1.93090978E-05 * t2m4 * rh2 + \
                  -3.08806365E-01 * va * rh2 + \
                  1.16952364E-02 * t2m * va * rh2 + \
                  4.95271903E-04 * t2m2 * va * rh2 + \
                  -1.90710882E-05 * t2m3 * va * rh2 + \
                  2.10787756E-03 * va2 * rh2 + \
                  -6.98445738E-04 * t2m * va2 * rh2 + \
                  2.30109073E-05 * t2m2 * va2 * rh2 + \
                  4.17856590E-04 * va3 * rh2 + \
                  -1.27043871E-05 * t2m * va3 * rh2 + \
                  -3.04620472E-06 * va4 * rh2 + \
                  5.14507424E-02 * e_mrt * rh2 + \
                  -4.32510997E-03 * t2m * e_mrt * rh2 + \
                  8.99281156E-05 * t2m2 * e_mrt * rh2 + \
                  -7.14663943E-07 * t2m3 * e_mrt * rh2 + \
                  -2.66016305E-04 * va * e_mrt * rh2 + \
                  2.63789586E-04 * t2m * va * e_mrt * rh2 + \
                  -7.01199003E-06 * t2m2 * va * e_mrt * rh2 + \
                  -1.06823306E-04 * va2 * e_mrt * rh2 + \
                  3.61341136E-06 * t2m * va2 * e_mrt * rh2 + \
                  2.29748967E-07 * va3 * e_mrt * rh2 + \
                  3.04788893E-04 * e_mrt2 * rh2 + \
                  -6.42070836E-05 * t2m * e_mrt2 * rh2 + \
                  1.16257971E-06 * t2m2 * e_mrt2 * rh2 + \
                  7.68023384E-06 * va * e_mrt2 * rh2 + \
                  -5.47446896E-07 * t2m * va * e_mrt2 * rh2 + \
                  -3.59937910E-08 * va2 * e_mrt2 * rh2 + \
                  -4.36497725E-06 * e_mrt3 * rh2 + \
                  1.68737969E-07 * t2m * e_mrt3 * rh2 + \
                  2.67489271E-08 * va * e_mrt3 * rh2 + \
                  3.23926897E-09 * e_mrt4 * rh2 + \
                  -3.53874123E-02 * rh3 + \
                  -2.21201190E-01 * t2m * rh3 + \
                  1.55126038E-02 * t2m2 * rh3 + \
                  -2.63917279E-04 * t2m3 * rh3 + \
                  4.53433455E-02 * va * rh3 + \
                  -4.32943862E-03 * t2m * va * rh3 + \
                  1.45389826E-04 * t2m2 * va * rh3 + \
                  2.17508610E-04 * va2 * rh3 + \
                  -6.66724702E-05 * t2m * va2 * rh3 + \
                  3.33217140E-05 * va3 * rh3 + \
                  -2.26921615E-03 * e_mrt * rh3 + \
                  3.80261982E-04 * t2m * e_mrt * rh3 + \
                  -5.45314314E-09 * t2m2 * e_mrt * rh3 + \
                  -7.96355448E-04 * va * e_mrt * rh3 + \
                  2.53458034E-05 * t2m * va * e_mrt * rh3 + \
                  -6.31223658E-06 * va2 * e_mrt * rh3 + \
                  3.02122035E-04 * e_mrt2 * rh3 + \
                  -4.77403547E-06 * t2m * e_mrt2 * rh3 + \
                  1.73825715E-06 * va * e_mrt2 * rh3 + \
                  -4.09087898E-07 * e_mrt3 * rh3 + \
                  6.14155345E-01 * rh4 + \
                  -6.16755931E-02 * t2m * rh4 + \
                  1.33374846E-03 * t2m2 * rh4 + \
                  3.55375387E-03 * va * rh4 + \
                  -5.13027851E-04 * t2m * va * rh4 + \
                  1.02449757E-04 * va2 * rh4 + \
                  -1.48526421E-03 * e_mrt * rh4 + \
                  -4.11469183E-05 * t2m * e_mrt * rh4 + \
                  -6.80434415E-06 * va * e_mrt * rh4 + \
                  -9.77675906E-06 * e_mrt2 * rh4 + \
                  8.82773108E-02 * rh5 + \
                  -3.01859306E-03 * t2m * rh5 + \
                  1.04452989E-03 * va * rh5 + \
                  2.47090539E-04 * e_mrt * rh5 + \
                  1.48348065E-03 * rh6

    utci_filtert2m = np.where((50 <= t2m <= -50 ))
    utci_filterva = np.where(( 17 <= va <=0))
    utci_filterrh = np.where((rh > 5))
    utci_filtere_mrt = np.where((70 <= e_mrt <=-30))
    utci_approx[utci_filtert2m] = -999
    utci_approx[utci_filterva] = -999
    utci_approx[utci_filterrh] = -999
    utci_approx[utci_filtere_mrt] = -999
    return utci_approx


def calculate_wbgts(t2m):
    """
    wgbts - Wet Bulb Globe Temperature Simple
    :param t2m: 2m temperature [K]
    :param rh: relative humidity [pa]

    https://link.springer.com/article/10.1007/s00484-011-0453-2
    http://www.bom.gov.au/info/thermal_stress/#approximation
    https://www.jstage.jst.go.jp/article/indhealth/50/4/50_MS1352/_pdf

    returns Wet Bulb Globe Temperature [°C]
    """
    t2m = __wrap(t2m)
    rh = calculate_relative_humidity(t2m)
    rh = __pa_to_hpa(rh)
    t2m = __kelvin_to_celcius(t2m)
    wbgts = 0.567 * t2m + 0.393 * rh + 3.38
    return (wbgts)


def calculate_wbgt(t2m, mrt, va):
    """
    calculate wet bulb globe temperature
    :param t2m: 2m temperature [K]
    :param mrt: mean radiant temperature [K]
    :param va: wind speed at 10 meters [m/s]

    returns wet bulb globe temperature [°C]
    """
    t2m = __wrap(t2m)
    mrt = __wrap(mrt)
    va = __wrap(va)

    f = (1.1e8 * va ** 0.6) / (0.98 * 0.15 ** 0.4)
    a = f / 2
    b = -f * t2m - mrt ** 4
    rt1 = 3 ** (1 / 3)
    rt2 = (np.sqrt(3) * np.sqrt(27 * a ** 4 - 16 * b ** 3) + 9 * a ** 2)
    rt3 = (2 * 2 ** (2 / 3) * b)
    va = va
    if va.any() <= 0:
        va = 0
    wbgt_quartic = - 1 / 2 * np.sqrt(rt3 / (rt1 * rt2 ** (1 / 3)) + \
                                     (2 ** (1 / 3) * rt2 ** (1 / 3)) / 3 ** (2 / 3)) + 1 / 2 * np.sqrt((4 * a) /
                                                                                                       np.sqrt(rt3 / (rt1 * rt2 ** (1 / 3)) + (2 ** (1 / 3) * rt2 ** (1 / 3)) / 3 **
                                                                                                               ( 2 / 3)) -(2 ** (1 / 3) * rt2 ** (1 / 3)) / 3 ** (2 / 3) - rt3 / (rt1 * rt2 ** ( 1 / 3)))
    wbgt_quartic = __kelvin_to_celcius(wbgt_quartic)
    return (wbgt_quartic)


def calculate_mrt_from_wbgt(t2m, wbgt, va):
    """
    calculate mean radiant temperature from wet bulb globe temperature
    :param t2m: 2m temperature [K]
    :param wbgt: wet bulb globe temperature in kelvin [K]
    :param va: wind speed at 10 meters [m/s]

    returns mean radiant temperature [K]
    """
    t2m = __wrap(t2m)
    wbgt = __wrap(wbgt)
    va = __wrap(va)

    f = (1.1e8 * va ** 0.6) / (0.98 * 0.15 ** 0.4)
    wbgt4 = wbgt ** 4
    dit = wbgt - t2m
    mrtcalculation = wbgt4 + f * dit
    mrtcalc2 = pow(mrtcalculation, 0.25)
    return (mrtcalc2)

def calculate_humidex(t2m, td):
    """
    humidex - heat index used by the Canadian Meteorological Serivce
    :param t2m: 2m temperature [K]
    :param td: dew point temperature [K]

    returns humidex [°C]
    """
    t2m = __wrap(t2m)
    td = __wrap(td)
    e = 6.11 * np.exp(5417.7530 * ((1 / t2m) - (1 / td)))
    h = 0.5555 * (e - 10.0)
    humidex = (t2m + h) - 273.15
    return humidex


def calculate_net_effective_temperature(t2m, rh, va):
    """
    Net Effective Temperature used in Hong Kong, Poland and Germany
    :param t2m: 2m temperature [K]
    :param rh: Relative Humidity [pa]
    :param va: Wind speed at 10 meters [m/s]

    returns net effective temperature [°C]
    """
    t2m = __wrap(t2m)
    va = __wrap(va)
    rh = __wrap(rh)
    t2m = __kelvin_to_celcius(t2m)
    rh = __pa_to_hpa(rh)
    #va = va * 4.87 / np.log10(67.8 * 10 - 5.42)  # converting to 2m, ~1.2m wind speed
    ditermeq = 1 / 1.76 + 1.4 * va ** 0.75
    net = 37 - (37 - t2m / 0.68 - 0.0014 * rh + ditermeq) - 0.29 * t2m * (1 - 0.01 * rh)
    return net


def calculate_apparent_temperature(t2m, rh, va):
    """
    Apparent Temperature version without radiation
    :param t2m: 2m Temperature [K]
    :param rh: Relative Humidity [pa]

    returns apparent temperature [K]
    """
    t2m = __wrap(t2m)
    va = __wrap(va)
    rh = __wrap(rh)
    va = va * 4.87 / np.log10(67.8 * 10 - 5.42)  # converting to 2m, ~1.2m wind speed
    at = t2m + 0.33 * rh - 0.7 * va - 4
    at = np.round(at,4)
    return at


def calculate_wind_chill(t2m, va):
    """
    Wind Chill
    :param t2m: 2m Temperature [K]
    :param rh: Relative Humidity [pa]
    :param va: wind speed at 10 meters [m/s]

    returns wind chill [°C]
    """
    t2m = __wrap(t2m)
    va = __wrap(va)
    t2m = __kelvin_to_celcius(t2m)
    va = va * 4.87 / np.log10(67.8 * 10 - 5.42)  # converting to 2m, ~1.2m wind speed
    va = va * 2.23694  # convert to miles per hour
    windchill = 13.12 + 0.6215 * t2m - 11.37 * va ** 0.16 + 0.3965 + t2m + va ** 0.16
    return windchill
