import sys
import numpy as np

from thermofeel.thermofeel import *
from thermofeel.grib import *

def calc_cossza(message):
    
    lats = message["lats"]
    lons = message["lons"]
    assert lats.size == lons.size

    print(lats.size)

    dt = message["datetime"]
    date = message["date"]
    time = message["time"]
    step = message["step"]

    print(dt.year, dt.month, dt.day, dt.hour)

    # scalar computation
    # cossza = []
    # for i in range(len(lats)):
    #     v = calculate_cos_solar_zenith_angle_integrated(lat=lats[i], lon=lons[i], y=dt.year, m=dt.month, d=dt.day, h=dt.hour, base=time / 100, step=3)
    #     # v = calculate_cos_solar_zenith_angle(lat=lats[i], lon=lons[i], y=dt.year, m=dt.month, d=dt.day, h=dt.hour)
    #     cossza.append(v)

    shape = (message["Nj"], message["Ni"])

    latsmat = np.reshape(lats, shape)
    lonsmat = np.reshape(lons, shape)

    # simpsons rule
    t = [dt.hour - 6, dt.hour, dt.hour + 6]
    w = (((dt.hour + 6) - (dt.hour - 6)) / 6) * np.array([1, 4, 1])

    print("t = ", t)
    print("w = ", w)

    integral = np.zeros(shape)

    for n in range(len(w)):
        cossza = calculate_cos_solar_zenith_angle(lat=lats, lon=lons, y=dt.year, m=dt.month, d=dt.day, h=t[n])
        integral += w[n] * np.reshape(cossza, shape)

    fname = sys.argv[2]
    print('=> ', fname)
    np.savez(fname, lats=latsmat, lons=lonsmat, values=integral)



def main():
    try:
        msgs = decode_grib(sys.argv[1])
        print(msgs)
        for m in msgs:
            calc_cossza(m)

    except eccodes.CodesInternalError as err:
        if eccodes.VERBOSE:
            eccodes.traceback.print_exc(file=sys.stderr)
        else:
            sys.stderr.write(err.msg + '\n')

        return 1


if __name__ == "__main__":
    sys.exit(main())