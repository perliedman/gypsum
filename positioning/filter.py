def ema(s, n):
    """
    returns an n period exponential moving average for
    the time series s

    s is a list ordered from oldest (index 0) to most
    recent (index -1)
    n is an integer

    returns a numeric array of the exponential
    moving average

    source: http://osdir.com/ml/python.matplotlib.general/2005-04/msg00044.html
    """
    ema = []
    j = 1

    if len(s) <= 1:
        return s

    n = min(len(s) - 1, n)

    #get n sma first and calculate the next n period ema
    sma = sum(s[:n]) / n
    multiplier = 2 / float(1 + n)
    ema.append(sma)

    #EMA(current) = ( (Price(current) - EMA(prev) ) x Multiplier) + EMA(prev)
    ema.append(( (s[n] - sma) * multiplier) + sma)

    #now calculate the rest of the values
    for i in s[n+1:]:
       tmp = ( (i - ema[j]) * multiplier) + ema[j]
       j = j + 1
       ema.append(tmp)

    return ema
