import sys as _sys
import numpy as _np

from .dynqt import QtGui as _qt

from .dynqt import qt as _qt_driver
if _qt_driver.name() == 'PythonQt':
    from .qimageview import QImage2ndarray as _temp
    _qimageview = _temp.qimageview
else:
    from .qimageview_python import qimageview as _qimageview

__version__ = "1.7"

if _sys.byteorder == 'little':
    _bgra = (0, 1, 2, 3)
else:
    _bgra = (3, 2, 1, 0)

_bgra_fields = {'b': (_np.uint8, _bgra[0], 'blue'),
                'g': (_np.uint8, _bgra[1], 'green'),
                'r': (_np.uint8, _bgra[2], 'red'),
                'a': (_np.uint8, _bgra[3], 'alpha')}

bgra_dtype = _np.dtype(_bgra_fields)
"""Complex dtype offering the named fields 'r','g','b', and 'a' and
corresponding long names, conforming to QImage_'s 32-bit memory layout."""

try:
    _basestring = basestring
except NameError:
    # 'basestring' undefined, must be Python 3
    _basestring = str

def _qimage_or_filename_view(qimage):
    if isinstance(qimage, _basestring):
        qimage = _qt.QImage(qimage)
    return _qimageview(qimage)

def raw_view(qimage):
    """Returns raw 2D view of the given QImage_'s memory.  The result
    will be a 2-dimensional numpy.ndarray with an appropriately sized
    integral dtype.  (This function is not intented to be used
    directly, but used internally by the other -- more convenient --
    view creation functions.)

    :param qimage: image whose memory shall be accessed via NumPy
    :type qimage: QImage_
    :rtype: numpy.ndarray_ with shape (height, width)"""
    return _qimage_or_filename_view(qimage)


def byte_view(qimage, byteorder = 'little'):
    """Returns raw 3D view of the given QImage_'s memory.  This will
    always be a 3-dimensional numpy.ndarray with dtype numpy.uint8.
    
    Note that for 32-bit images, the last dimension will be in the
    [B,G,R,A] order (if little endian) due to QImage_'s memory layout
    (the alpha channel will be present for Format_RGB32 images, too).

    For 8-bit (indexed) images, the array will still be 3-dimensional,
    i.e. shape will be (height, width, 1).

    The order of channels in the last axis depends on the `byteorder`,
    which defaults to 'little', i.e. BGRA order.  You may set the
    argument `byteorder` to 'big' to get ARGB, or use None which means
    sys.byteorder here, i.e. return native order for the machine the
    code is running on.

    For your convenience, `qimage` may also be a filename, see
    `Loading and Saving Images`_ in the documentation.

    :param qimage: image whose memory shall be accessed via NumPy
    :type qimage: QImage_
    :param byteorder: specify order of channels in last axis
    :rtype: numpy.ndarray_ with shape (height, width, 1 or 4) and dtype uint8"""
    raw = _qimage_or_filename_view(qimage)
    result = raw.view(_np.uint8).reshape(raw.shape + (-1, ))
    if byteorder and byteorder != _sys.byteorder:
        result = result[...,::-1]
    return result


def rgb_view(qimage, byteorder = 'big'):
    """Returns RGB view of a given 32-bit color QImage_'s memory.
    Similarly to byte_view(), the result is a 3D numpy.uint8 array,
    but reduced to the rgb dimensions (without alpha), and reordered
    (using negative strides in the last dimension) to have the usual
    [R,G,B] order.  The image must have 32 bit pixel size, i.e. be
    RGB32, ARGB32, or ARGB32_Premultiplied.  (Note that in the latter
    case, the values are of course premultiplied with alpha.)

    The order of channels in the last axis depends on the `byteorder`,
    which defaults to 'big', i.e. RGB order.  You may set the argument
    `byteorder` to 'little' to get BGR, or use None which means
    sys.byteorder here, i.e. return native order for the machine the
    code is running on.

    For your convenience, `qimage` may also be a filename, see
    `Loading and Saving Images`_ in the documentation.

    :param qimage: image whose memory shall be accessed via NumPy
    :type qimage: QImage_ with 32-bit pixel type
    :param byteorder: specify order of channels in last axis
    :rtype: numpy.ndarray_ with shape (height, width, 3) and dtype uint8"""
    if byteorder is None:
        byteorder = _sys.byteorder
    bytes = byte_view(qimage, byteorder)
    if bytes.shape[2] != 4:
        raise ValueError("For rgb_view, the image must have 32 bit pixel size (use RGB32, ARGB32, or ARGB32_Premultiplied)")

    if byteorder == 'little':
        return bytes[...,:3] # strip A off BGRA
    else:
        return bytes[...,1:] # strip A off ARGB


def alpha_view(qimage):
    """Returns alpha view of a given 32-bit color QImage_'s memory.
    The result is a 2D numpy.uint8 array, equivalent to
    byte_view(qimage)[...,3].  The image must have 32 bit pixel size,
    i.e. be RGB32, ARGB32, or ARGB32_Premultiplied.  Note that it is
    not enforced that the given qimage has a format that actually
    *uses* the alpha channel -- for Format_RGB32, the alpha channel
    usually contains 255 everywhere.

    For your convenience, `qimage` may also be a filename, see
    `Loading and Saving Images`_ in the documentation.

    :param qimage: image whose memory shall be accessed via NumPy
    :type qimage: QImage_ with 32-bit pixel type
    :rtype: numpy.ndarray_ with shape (height, width) and dtype uint8"""
    bytes = byte_view(qimage, byteorder = None)
    if bytes.shape[2] != 4:
        raise ValueError("For alpha_view, the image must have 32 bit pixel size (use RGB32, ARGB32, or ARGB32_Premultiplied)")
    return bytes[...,_bgra[3]]


def recarray_view(qimage):
    """Returns recarray_ view of a given 32-bit color QImage_'s
    memory.

    The result is a 2D array with a complex record dtype, offering the
    named fields 'r','g','b', and 'a' and corresponding long names.
    Thus, each color components can be accessed either via string
    indexing or via attribute lookup (through numpy.recarray_):

    For your convenience, `qimage` may also be a filename, see
    `Loading and Saving Images`_ in the documentation.

    >>> from PyQt4.QtGui import QImage, qRgb
    >>> qimg = QImage(320, 240, QImage.Format_ARGB32)
    >>> qimg.fill(qRgb(12,34,56))
    >>>
    >>> import qimage2ndarray
    >>> v = qimage2ndarray.recarray_view(qimg)
    >>>
    >>> red = v["r"]
    >>> red[10,10]
    12
    >>> pixel = v[10,10]
    >>> pixel["r"]
    12
    >>> (v.g == v["g"]).all()
    True
    >>> (v.alpha == 255).all()
    True

    :param qimage: image whose memory shall be accessed via NumPy
    :type qimage: QImage_ with 32-bit pixel type
    :rtype: numpy.ndarray_ with shape (height, width) and dtype :data:`bgra_dtype`"""
    raw = _qimage_or_filename_view(qimage)
    if raw.itemsize != 4:
        raise ValueError("For rgb_view, the image must have 32 bit pixel size (use RGB32, ARGB32, or ARGB32_Premultiplied)")
    return raw.view(bgra_dtype, _np.recarray)



def _normalize255(array, normalize, clip = (0, 255)):
    if normalize:
        if normalize is True:
            normalize = array.min(), array.max()
            if clip == (0, 255):
                clip = None
        elif _np.isscalar(normalize):
            normalize = (0, normalize)

        nmin, nmax = normalize

        if nmin:
            array = array - nmin

        if nmax != nmin:
            scale = 255. / (nmax - nmin)
            if scale != 1.0:
                array = array * scale

    if clip:
        low, high = clip
        _np.clip(array, low, high, array)

    return array


def gray2qimage(gray, normalize = False):
    """Convert the 2D numpy array `gray` into a 8-bit, indexed QImage_
    with a gray colormap.  The first dimension represents the vertical
    image axis.

    The parameter `normalize` can be used to normalize an image's
    value range to 0..255:

    `normalize` = (nmin, nmax):
      scale & clip image values from nmin..nmax to 0..255

    `normalize` = nmax:
      lets nmin default to zero, i.e. scale & clip the range 0..nmax
      to 0..255

    `normalize` = True:
      scale image values to 0..255 (same as passing (gray.min(),
      gray.max()))

    If the source array `gray` contains masked values, the result will
    have only 255 shades of gray, and one color map entry will be used
    to make the corresponding pixels transparent.

    A full alpha channel cannot be supported with indexed images;
    instead, use `array2qimage` to convert into a 32-bit QImage.

    :param gray: image data which should be converted (copied) into a QImage_
    :type gray: 2D or 3D numpy.ndarray_ or `numpy.ma.array <masked arrays>`_
    :param normalize: normalization parameter (see above, default: no value changing)
    :type normalize: bool, scalar, or pair
    :rtype: QImage_ with RGB32 or ARGB32 format"""
    if _np.ndim(gray) != 2:
        raise ValueError("gray2QImage can only convert 2D arrays" +
                         " (try using array2qimage)" if _np.ndim(gray) == 3 else "")

    h, w = gray.shape
    result = _qt.QImage(w, h, _qt.QImage.Format_Indexed8)

    if not _np.ma.is_masked(gray):
        for i in range(256):
            result.setColor(i, _qt.qRgb(i,i,i))

        _qimageview(result)[:] = _normalize255(gray, normalize)
    else:
        # map gray value 1 to gray value 0, in order to make room for
        # transparent colormap entry:
        result.setColor(0, _qt.qRgb(0,0,0))
        for i in range(2, 256):
            result.setColor(i-1, _qt.qRgb(i,i,i))

        _qimageview(result)[:] = _normalize255(gray, normalize, clip = (1, 255)) - 1

        result.setColor(255, 0)
        _qimageview(result)[gray.mask] = 255

    return result


def array2qimage(array, normalize = False):
    """Convert a 2D or 3D numpy array into a 32-bit QImage_.  The
    first dimension represents the vertical image axis; the optional
    third dimension is supposed to contain 1-4 channels:

    ========= ===================
    #channels interpretation
    ========= ===================
            1 scalar/gray
            2 scalar/gray + alpha
            3 RGB
            4 RGB + alpha
    ========= ===================

    Scalar data will be converted into corresponding gray RGB triples;
    if you want to convert to an (indexed) 8-bit image instead, use
    `gray2qimage` (which cannot support an alpha channel though).

    The parameter `normalize` can be used to normalize an image's
    value range to 0..255:

    `normalize` = (nmin, nmax):
      scale & clip image values from nmin..nmax to 0..255

    `normalize` = nmax:
      lets nmin default to zero, i.e. scale & clip the range 0..nmax
      to 0..255

    `normalize` = True:
      scale image values to 0..255 (same as passing (array.min(),
      array.max()))

    If `array` contains masked values, the corresponding pixels will
    be transparent in the result.  Thus, the result will be of
    QImage.Format_ARGB32 if the input already contains an alpha
    channel (i.e. has shape (H,W,4)) or if there are masked pixels,
    and QImage.Format_RGB32 otherwise.

    :param array: image data which should be converted (copied) into a QImage_
    :type array: 2D or 3D numpy.ndarray_ or `numpy.ma.array <masked arrays>`_
    :param normalize: normalization parameter (see above, default: no value changing)
    :type normalize: bool, scalar, or pair
    :rtype: QImage_ with RGB32 or ARGB32 format"""
    if _np.ndim(array) == 2:
        array = array[...,None]
    elif _np.ndim(array) != 3:
        raise ValueError("array2qimage can only convert 2D or 3D arrays (got %d dimensions)" % _np.ndim(array))
    if array.shape[2] not in (1, 2, 3, 4):
        raise ValueError("array2qimage expects the last dimension to contain exactly one (scalar/gray), two (gray+alpha), three (R,G,B), or four (R,G,B,A) channels")

    h, w, channels = array.shape

    hasAlpha = _np.ma.is_masked(array) or channels in (2, 4)
    fmt = _qt.QImage.Format_ARGB32 if hasAlpha else _qt.QImage.Format_RGB32

    result = _qt.QImage(w, h, fmt)

    array = _normalize255(array, normalize)

    if channels >= 3:
        rgb_view(result)[:] = array[...,:3]
    else:
        rgb_view(result)[:] = array[...,:1] # scalar data

    alpha = alpha_view(result)

    if channels in (2, 4):
        alpha[:] = array[...,-1]
    else:
        alpha[:] = 255

    if _np.ma.is_masked(array):
        alpha[:]  *= _np.logical_not(_np.any(array.mask, axis = -1))

    return result


def imread(filename, masked = False):
    """Convenience function that uses the QImage_ constructor to read an
    image from the given file and return an `rgb_view` of the result.
    This is intentionally similar to scipy.ndimage.imread (which uses
    PIL), scipy.misc.imread, or matplotlib.pyplot.imread (using PIL
    for non-PNGs).

    For grayscale images, return 2D array (even if it comes from a 32-bit
    representation; this is a consequence of the QImage API).

    For images with an alpha channel, the resulting number of channels
    will be 2 (grayscale+alpha) or 4 (RGB+alpha).  Alternatively, one may
    pass `masked = True` in order to get `masked arrays`_ back.
    Note that only fully transparent pixels are masked
    (and that masked arrays only support binary masks).  The value of
    `masked` is ignored when the loaded image has no alpha channel
    (i.e., one would not get a masked array in that case).

    This function has been added in version 1.3.

    """
    qImage = _qt.QImage(filename)

    isGray = qImage.isGrayscale()
    if isGray and qImage.depth() == 8:
        return byte_view(qImage)[...,0]

    hasAlpha = qImage.hasAlphaChannel()

    if hasAlpha:
        targetFormat = _qt.QImage.Format_ARGB32
    else:
        targetFormat = _qt.QImage.Format_RGB32
    if qImage.format() != targetFormat:
        qImage = qImage.convertToFormat(targetFormat)

    result = rgb_view(qImage)
    if isGray:
        result = result[...,0]
    if hasAlpha:
        if masked:
            mask = (alpha_view(qImage) == 0)
            if _np.ndim(result) == 3:
                mask = _np.repeat(mask[...,None], 3, axis = 2)
            result = _np.ma.masked_array(result, mask)
        else:
            result = _np.dstack((result, alpha_view(qImage)))
    return result


def imsave(filename, image, normalize = False, format = None, quality = -1):
    """Convenience function that uses QImage.save to save an image to the
    given file.  This is intentionally similar to scipy.misc.imsave.
    However, it supports different optional arguments:

    :param normalize: see :func:`array2qimage` (which is used internally)
    :param format: image filetype (e.g. 'PNG'),  (default: check filename's suffix)
    :param quality: see QImage.save (0 = small .. 100 = uncompressed, -1 = default compression)
    :returns: boolean success, see QImage.save
    
    This function has been added in version 1.4.
    """
    qImage = array2qimage(image, normalize = normalize)
    return qImage.save(filename, format, quality)
