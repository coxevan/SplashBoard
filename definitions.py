import urllib2
import urllib
import webbrowser as wb
import simplejson
import socket
import os
import pymel.core as py
from PIL import Image


def google_image_search(**kwargs):
    """
    Queries google using JSON API using the parsed search results.

    Kwargs -
        search_term = no default
        page = 1*
        result_count = 7*
    Returns resulting dictionary from google image search

    Returns 1 if URL error
    Returns 2 if JSON error
    """
    search_term = kwargs.setdefault('search_term')
    page = kwargs.setdefault('page', 1)
    number_of_results = kwargs.setdefault('result_count', 7)
    ip_address = socket.gethostbyname(socket.gethostname())

    url = ('https://ajax.googleapis.com/ajax/services/search/images?' +
           'v=1.0&q=' + search_term +
           '&userip=' + ip_address +
           '&start=' + str(page) +
           '&rsz=' + str(number_of_results))
    try:
        request = urllib2.Request(url, None, {'Referer': 'http://www.evancox.net/'})
        response = urllib2.urlopen(request)
    except:
        py.warning("Could not complete request: Please check your internet connection.")
        #py.deleteUI(cls.search_frame)

        return 1
    try:
        results = simplejson.load(response)

        return results
    except:
        error = "Error loading json results into dictionary"
        py.warning(error)
        #py.deleteUI(cls.search_frame)

        return 2


def download_image_results(results, term):
    """
    Downloads image results from the google image search results.
    Saves in a temporary reference image directory located in the user's home directory.
        (If directory doesn't already exists, it is created)
    Dictionaries are created with attributes of the images, then all put in a list.

    Returns a list of dictionaries with the following keys:
        width (str)
        height (str)
        url (str)
        thumb_width (str)
        thumb_height (str)
        path (str)
        thumb_path (str)
        im_id (unique image ID provided by Google) (str)
        Downloaded (bool)
        search_term (str)
    """
    num = 0
    return_list = []
    search_directory = create_directories(term=term)

    for result in results['responseData']['results']:
        result_count = len(results['responseData']['results'])
        thumb_path = os.path.join(search_directory, result['imageId']+'_thumbnail.png')
        if not os.path.exists(thumb_path):
            try:
                urllib.urlretrieve(result['unescapedUrl'], search_directory + result['imageId'] + '.png')
            except IOError:
                py.warning('Cannot download some images. Check your internet connection!')
            attr_dict = {'width': result['width'],
                         'height': result['height'],
                         'url': result['unescapedUrl'],
                         'thumb_width': result['tbWidth'],
                         'thumb_height': result['tbHeight'],
                         'path': os.path.join(search_directory, result['imageId']+'.png'),
                         'thumb_path': thumb_path,
                         'im_id': result['imageId'],
                         'downloaded': True,
                         'search_term': term}
            make_thumbnail(attr_dict['path'], thumbPath=thumb_path)
            num += 1
            print "Processed & Downloaded %i out of %i for %s" % (num, result_count, term)
        else:
            path = os.path.join(search_directory, result['imageId']+'.png')
            im = Image.open(path)
            width, height = im.size

            attr_dict = downloaded_image_dictionary(path=path,
                                      thumb_path=thumb_path,
                                      imageId=result['imageId'],
                                      term=term,
                                      width=width,
                                      height=height)
        return_list.append(attr_dict)

    return return_list


def make_thumbnail(path, **kwargs):
    """
    Uses PIL to create thumbnails.
    Kwargs -
        thumbSize = Tuple, (200,200)*
        thumbPath = str
        returnWidthHeight = False*

    Returns widthHeight tuple of new thumbnail if returnWidthHeight is True
    Returns 1 if exception raised
    Else Returns 0
    """
    thumb_size = kwargs.setdefault('thumbSize', (200, 200))
    thumb_path = kwargs.setdefault('thumbPath')
    width_height_bool = kwargs.setdefault('returnWidthHeight', False)
    try:
        im = Image.open(path)
        im.thumbnail(thumb_size, Image.ANTIALIAS)
        im.save(thumb_path, "PNG")
        if width_height_bool is True:
            return im.size
    except:
        os.remove(path)
        return 1

    return 0


def downloaded_image_dictionary(**kwargs):
    """
    Dictionary creation for images that were previously downloaded/custom images.

    Returns created dictionary
    """
    path = kwargs.setdefault('path')
    thumb_path = kwargs.setdefault('thumb_path')
    im_id = kwargs.setdefault('imageId')
    search_term = kwargs.setdefault('term')
    width = kwargs.setdefault('width')
    height = kwargs.setdefault('height')

    dictionary = {'path': path,
                         'thumb_path': thumb_path,
                         'im_id': im_id,
                         'downloaded': False,
                         'search_term': search_term,
                         'width': width,
                         'height': height}

    return dictionary


def reference_plane(flip, **kwargs):
    """
    Creates reference planes based on kwargs and boolean "flip"

    If height of image is greater than or equal to 700, scaleFactor of 0.25 is applied.

    Kwargs -
        axis - (1, 2, 3) for (X, Y, Z)
        dict - image dictionary
        term - search term
        width - image width
        height - image height
        scaleFactor - 1*
        
    Returns reference plane
    """
    fallback_dict = {'path': "", "width": 0, "height": 0}
    radio = kwargs.setdefault('axis')
    image_dict = kwargs.setdefault('dict', fallback_dict)
    name = kwargs.setdefault('term')+'_reference'
    path = kwargs.setdefault('path', image_dict['path'])
    material = create_material(path)
    scale_factor = kwargs.setdefault('scaleFactor', 1)

    dict_width = float(image_dict['width'])
    dict_height = float(image_dict['height'])

    width = kwargs.setdefault('width', dict_width)
    height = kwargs.setdefault('height', dict_height)
    print height
    if height >= 700:
        scale_factor = 0.25

    width *= scale_factor
    height *= scale_factor

    if radio is 3:
        plane = py.polyPlane(n=name, ax=(0, 0, 1), w=width, h=height, sx=1, sy=1)[0]
        py.move(0, (0.5*height), 0, plane)
        py.xform(plane, piv=(0, -0.5*height, 0))
    elif radio is 2:
        plane = py.polyPlane(n=name, ax=(0, 1, 0), w=width, h=height, sx=1, sy=1)[0]
    else:
        plane = py.polyPlane(n=name, ax=(1, 0, 0), w=width, h=height, sx=1, sy=1)[0]
        py.move(0, (0.5*height), 0, plane)
        py.xform(plane, piv=(0, -0.5*height, 0))
    if flip is True:
        py.setAttr(plane+'.scaleZ', -1)
    apply_material(plane, material, freeze=True)
    reference_layer(plane)

    return plane


def apply_material(objects, material, **kwargs):
    """
    Apply a material to an object

    Returns 0
    """
    freeze_bool = kwargs.setdefault('freeze', False)
    py.select(objects)
    py.hyperShade(assign=material)
    if freeze_bool is True:
        py.delete(ch=True)
        py.makeIdentity(apply=True, t=1, r=1, s=1, n=0)
        py.select(cl=True)

    return 0


def create_material(filepath, **kwargs):
    """
    Creates material to be applied later.
    Kwargs -
        name = 'refMaterial'
        material_type = 'lambert'

    Returns new material
    """
    name = kwargs.setdefault('name', 'refMaterial')
    material_type = kwargs.setdefault('material_type', 'lambert')
    material = py.shadingNode(material_type, asShader=True, n=name)
    alpha_value = kwargs.setdefault('alpha', 0.5)

    shader_group = py.sets(material, renderable=True, noSurfaceShader=True, empty=True)
    py.connectAttr((material + ".outColor"), (shader_group + ".surfaceShader"), f=True)
    py.setAttr((material+".transparency"), alpha_value, alpha_value, alpha_value, type="double3")

    img = py.shadingNode('file', asTexture=True)
    py.setAttr(img+'.fileTextureName', filepath, type='string')
    py.connectAttr(img+'.outColor', material+'.color', force=True)

    return material


def image_plane(path, **kwargs):
    """
    Creates an image plane from the path provided. Width and height optional but highly recommended.

    Returns new image plane
    """
    width_height = kwargs.setdefault('widthHeight', (100, 100))
    image_plane_xform = py.imagePlane(width=width_height[0], height=width_height[1])[0]

    py.setAttr("%s.imageName" % image_plane_xform, path, type="string")
    reference_layer(image_plane_xform)

    return image_plane_xform


def apply_as_texture(**kwargs):
    """
    Creates & applies material with image as texture to an object

    Returns 0
    """
    fallback_dict = {"search_term": " ", "path": " "}
    image_dict = kwargs.setdefault('dict', fallback_dict)
    selected = py.ls(sl=True)
    name = kwargs.setdefault('name', image_dict['search_term'])
    path = kwargs.setdefault('path', image_dict['path'])
    alpha_value = kwargs.setdefault('alpha', 0)
    material_name = name+'_material'

    material = create_material(path, name=material_name, alpha=alpha_value)
    apply_material(selected, material)

    return 0


def reference_layer(object, **kwargs):
    """
    Creates reference layer "Ref_Layer" if not already made or no new name is provided
    Adds object to new layer

    Returns new reference layer
    """
    layer = kwargs.setdefault('name', 'Ref_Layer')
    if py.objExists(layer) is False:
        py.createDisplayLayer(empty=True, n=layer)
        py.setAttr(layer+".dt", 2)
    py.editDisplayLayerMembers(layer, object)

    return layer


def create_directories(**kwargs):
    """
    Checks and creates directories needed for image and thumbnail storage.

    Returns 0
    """
    search_bool = kwargs.setdefault('search', True)
    temp_directory = os.path.expanduser('~/') + 'temp_reference_images/'
    custom_directory = os.path.join(temp_directory, "custom_images"+'/')

    if not os.path.exists(temp_directory):
            os.makedirs(temp_directory)

    if not os.path.exists(custom_directory):
        os.makedirs(custom_directory)

    if search_bool is True:
        term = kwargs.setdefault('term')
        search_directory = os.path.join(temp_directory, term+'/')
        if not os.path.exists(search_directory):
            os.makedirs(search_directory)
        return search_directory

    if search_bool is False:
        image_name = kwargs.setdefault('image_name')
        thumb_path = os.path.join(custom_directory, image_name)
        return thumb_path

    return 0


def open_url(url):
    """
    Uses urllib2 to open URL's for extenal libs

    Returns 0
    """
    wb.open(url)
    return 0