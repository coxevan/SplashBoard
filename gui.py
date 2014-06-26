import maya.cmds as mc
import pymel.core as py
import definitions as df
import os
from shutil import rmtree


class SplashBoard(object):
    def __init__(self):
        self.window_name = ''
        self.window_title = ''
        self.win = ''
        self.vert_col = ''
        self.text_field = ''
        self.already_searched = []

    def gui(self):
        """
        Creates main GUI for SplashBoard script.
        Calls self.dock_gui() at the end to dock the UI into Maya's mainWindow

        Variables affected:
            self.window_name
            self.window_title
            self.win
            self.vert_col
            self.text_field

        Local variables (button, scroll, image_column) created but not used for expansion of additional features.

        Returns 0
        """
        self.window_name = 'splash_ec_window'
        self.window_title = 'SplashBoard'
        dock_control = 'splashDock'

        if py.window(self.window_name, exists=True):
            py.deleteUI(self.window_name, window=True)

        if py.dockControl(dock_control, exists=True):
            py.deleteUI(dock_control)

        self.win = py.window(self.window_name, title=self.window_title, menuBar=True)
        file_menu = py.menu('File', p=self.win)
        delete_submenu = py.menuItem('Delete', subMenu=True, p=file_menu)
        py.menuItem('Delete Temporary Downloads Folder', p=delete_submenu, command=py.Callback(self.delete_dir))
        py.menuItem('Delete All Results', p=delete_submenu, command=py.Callback(self.delete_all_frame))
        py.menuItem(divider=True, p=file_menu)

        help_menu = py.menu('Help', p=self.win)
        py.menuItem('Open Documentation', p=help_menu, command=py.Callback(df.open_url, "http://www.evancox.net/"))
        py.menuItem('About SplashBoard', p=help_menu, command=py.Callback(df.open_url, "http://www.evancox.net/"))
        py.menuItem(divider=True, p=help_menu)
        py.menuItem('EvanCox.net', p=help_menu, command=py.Callback(df.open_url, "http://www.evancox.net/"))

        master_column = py.formLayout('master_form', nd=100)
        google_row = py.rowLayout('google_row', p=master_column, numberOfColumns=3)
        button = py.button('google_button', l='Populate Images: Powered by Google', p=google_row, command=py.Callback(self.parse_terms))
        self.text_field = py.textField('google_text', tx='Search Terms Separated by commas', p=google_row, w=200)


        scroll = py.scrollLayout('image_scroll', p=master_column)
        image_column = py.columnLayout('image_column')
        self.vert_col = py.verticalLayout(ratios=[0, 0, 0])

        py.menuItem('Insert Custom Images', p=file_menu, command=py.Callback(SearchResults, custom=True,
                                                                             column=self.vert_col,
                                                                             searchTerm='Custom'))

        master_column.attachForm('google_row', 'top', 5)
        master_column.attachForm('image_scroll', 'bottom', 5)
        master_column.attachForm('image_scroll', 'right', 5)
        master_column.attachForm('image_scroll', 'left', 5)
        master_column.attachControl('image_scroll', 'top', 4, 'google_row')
        self.dock_gui()

        return 0

    def dock_gui(self):
        """
        Dock's GUI into Maya's main window.

        Returns the dock pymel object
        """
        py.toggleWindowVisibility(self.window_name)
        pane_layout = py.paneLayout(configuration='single')
        dock = py.dockControl('splashDock', label=self.window_title, area='left', content=pane_layout)
        py.control(self.window_name, e=True, p=pane_layout)

        return dock

    def parse_terms(self):
        """
        Retrieves text field information and splits based on comma's.

        For each term in the search query, replaces " " with "%20" for JSON
        Checks if a frame with those results already exists.

        If passes, creates an instance of class SearchResult with converted_term, term and the vertical column

        If any RuntimeError occurs during the SearchResult initialization, exception passed through py.warning to the user

        Returns 0
        """
        un_parsed = self.text_field.getText()
        split = un_parsed.split(', ')
        for term in split:
            converted_term = term.replace(' ', '%20')
            if py.frameLayout(term+"_frame", exists=True):
                py.warning('You have already searched for %s' % term)
            else:
                try:
                    search = SearchResults(convertedTerm=converted_term, searchTerm=term, column=self.vert_col)
                except RuntimeError as error:
                    py.warning(error)
            self.already_searched.append(term)

        return 0

    def delete_dir(self):
        """
        Deletes user's temporary reference image directory.
        Directory located in: [USER HOME DIRECTORY]/temp_reference_images/
        """
        temp_directory = os.path.expanduser('~/') + 'temp_reference_images/'
        rmtree(temp_directory)

        return 0

    def delete_all_frame(self):
        """
        Deletes all frames from searches.

        If frame for term in self.already_searched does not exist, it is skipped (assuming error)
        self.already_searched is then cleared.
        """
        for term in self.already_searched:
            try:
                py.deleteUI(term+"_frame")
            except:
                pass
        self.already_searched = []

        return 0


class SearchResults(object):
    def __init__(self, **kwargs):
        self.current_page = 1
        self.result_count = 8
        self.image_layouts = []
        self.term = kwargs.setdefault('searchTerm')
        self.converted_term = kwargs.setdefault('convertedTerm')
        self.parent = kwargs.setdefault('column')
        self.search_frame = ''
        self.search_column = ''
        self.custom = kwargs.setdefault('custom', False)
        self.custom_image_path_list = []
        self.custom_image_thumb_path_list = []
        self.custom_horizontal_layout = ''
        self.title_list = [["", "Side View (Down X)", "Top View (Down Y)", "Front View (Down Z)"],
                ["", "Create Plane (+Z)", "Create Plane (+Z)", "Create Plane (+X)"],
                ["", "Create Plane (-Z)", "Create Plane (-Z)", "Create Plane (-X)"]]

        if self.custom is False:
            self.gui_creation()
        else:
            self.custom_image_gui()

    def gui_creation(self):
        self.search_frame = py.frameLayout('%s_frame' % self.term, label=self.term, p=self.parent, cll=True,
                                           cc=py.Callback(self.parent.redistribute),
                                           ec=py.Callback(self.parent.redistribute))
        self.search_column = py.columnLayout('%s_column' % self.term, p=self.search_frame)
        self.google_search(self.converted_term, self.term, self.current_page)
        self.utility_buttons()
        self.parent.redistribute()

    def google_search(self, converted_term, term, current_page):
        """
        Performs google search. Needs a converted term ("%20" instead of " "), raw term and current_page)

        Returns 0 if success
        Returns 1 if search results are not of type dict
        Returns 2 if downloaded images are not of type list
        """
        search_results = df.google_image_search(self, search_term=converted_term, result_count=self.result_count,
                                                page=current_page)
        print search_results
        if not isinstance(search_results, dict):
            return 1

        result_list = df.download_image_results(search_results, converted_term)

        if not isinstance(result_list, list):
            return 2

        row_list = self.list_chunk(result_list, self.result_count/2)
        self.image_layouts = []
        for row in row_list:
            self.image_layouts.append(self.create_images(row, term))

        return 0

    def create_images(self, images_in_row, term):
        layout = py.horizontalLayout(p=self.search_column, ratios=[0, 0, 0])
        for i in range(0, len(images_in_row)):
            image_name = term.replace(' ', '_')+'_image_%i' % i

            py.image(image_name, p=layout, i=images_in_row[i]['thumb_path'])

            image_menu = py.popupMenu(image_name+'_menu', p=image_name, ctl=False, button=3)

            py.menuItem('Pop out', p=image_menu, c=py.Callback(self.pop_out_gui, images_in_row[i]['path']))

            reference_submenu = py.menuItem('polyPlane Reference', p=image_menu, subMenu=True)
            for k in xrange(1, 4):
                view_submenu = py.menuItem(self.title_list[0][k], subMenu=True, p=reference_submenu)
                py.menuItem(self.title_list[1][k], p=view_submenu, c=py.Callback(df.reference_plane, False,
                                                                                              axis=k,
                                                                                              dict=images_in_row[i],
                                                                                              term=term.replace(' ', '_'),
                                                                                              scaleFactor=0.5))
                py.menuItem(self.title_list[2][k], p=view_submenu, c=py.Callback(df.reference_plane, True,
                                                                                              axis=k,
                                                                                              dict=images_in_row[i],
                                                                                              term=term.replace(' ', '_'),
                                                                                              scaleFactor=0.5))

            image_plane_submenu = py.menuItem('Image Plane Reference', p=image_menu, subMenu=True)
            py.menuItem('Create Image Plane', p=image_plane_submenu, c=py.Callback(df.image_plane,
                                                                                   images_in_row[i]['path'],
                                                                                   widthHeight=(int(images_in_row[i]['width']),
                                                                                                int(images_in_row[i]['height']))))

            py.menuItem('Apply as Texture', p=image_menu, c=py.Callback(df.apply_as_texture, dict=images_in_row[i]))

            py.menuItem('Delete Image', p=image_menu, c=py.Callback(py.deleteUI, image_name))
        layout.redistribute()

        return layout

    def list_chunk(self, to_split, chunk_size):
        """
        Returns images split into groups for placement into rows in SearchResult GUI.
        """
        if chunk_size < 1:
            chunk_size = 1

        return [to_split[i:i+chunk_size] for i in range(0, len(to_split), chunk_size)]

    def pop_out_gui(self, imagepath):
        window = 'pop_out_gui'

        if py.window(window, exists=True):
            py.deleteUI(window, window=True)

        self.win = py.window(window, title='SplashBoard: Pop out')
        image_row = py.rowLayout(numberOfColumns=2)
        py.image('image_pop_out', p=image_row, i=imagepath)
        self.win.show()

        return 0

    def utility_buttons(self):
        """
        Creates buttons/sub menu's: Delete Results, Previous and Next Page

        Returns 0
        """

        row_layout = py.rowLayout('utility_button_row', p=self.search_frame, numberOfColumns=3)
        delete_button = py.button(label='Delete Results', c=py.Callback(self.delete_results))

        if self.custom is False:
            del_menu = py.popupMenu(p=delete_button, ctl=False, button=3)
            py.menuItem('Delete Images and Search Directory', p=del_menu,
                        c=py.Callback(self.delete_results, deleteDirectory=True))
            py.button(label='Previous Page', c=py.Callback(self.new_results, operation='sub'))
            py.button(label='Next Page', c=py.Callback(self.new_results))
        else:
            py.button(label='Insert New Image', c=py.Callback(self.add_custom_image))

        return 0

    def new_results(self, **kwargs):
        """
        Handles the creation of new images inside the SearchResult class.
        Kwargs -
            operation = 'add'* , 'sub'

        Returns 0
        """
        operation = kwargs.setdefault('operation', 'add')
        try:
            py.deleteUI(self.image_layouts)
        except:
            pass
        if operation == 'add':
            self.current_page += self.result_count

        if operation == 'sub':
            if self.current_page < 9:
                py.warning('Can not go back any further in image results')
            else:
                self.current_page -= self.result_count
        self.google_search(self.converted_term, self.term, self.current_page)

        return 0

    def delete_results(self, **kwargs):
        """
        Deletes the current result frame
        Optionally deletes the current result frame AND respective temp image directory.

        Returns 0
        """
        dir_bool = kwargs.setdefault('deleteDirectory', False)
        py.deleteUI(self.search_frame)
        if dir_bool is True:
            temp_directory = os.path.expanduser('~/') + 'temp_reference_images/'
            search_directory = os.path.join(temp_directory, self.term+'/')
            rmtree(search_directory)

        return 0

    def custom_image_gui(self):
        """
        Creation of GUI to hold custom images

        Returns 0
        Returns 1 if already exists (RuntimeError)
        """
        try:
            self.search_frame = py.frameLayout('custom_image_frame', label="Custom Images", p=self.parent, cll=True,
                                               cc=py.Callback(self.parent.redistribute),
                                               ec=py.Callback(self.parent.redistribute))
            self.search_column = py.columnLayout('custom_column', p=self.search_frame)
            #self.google_search(self.converted_term, self.term, self.current_page)
            self.utility_buttons()
            self.parent.redistribute()

            return 0
        except RuntimeError:
            return 1

    def find_custom_image(self):
        """
        Prompts user with file dialogue to find custom image.
        Returns list with [path, thumbnail_path, name of image, (width, height)]
        """
        path = mc.fileDialog(title="Locate your Image!")
        image_path_conversion = path.replace('\\', '/')
        image_name = image_path_conversion.split('/')[-1]

        thumb_path = df.create_directories(search=False, image_name=image_name)
        width_height = df.make_thumbnail(path, thumbPath=thumb_path, returnWidthHeight=True)

        return [path, thumb_path, image_name, width_height]

    def add_custom_image(self):
        """
        Adds custom images to UI

        Returns 0
        """

        image_attr_list = self.find_custom_image()
        path = image_attr_list[0]
        thumb_path = image_attr_list[1]
        width = image_attr_list[3][0]
        height = image_attr_list[3][1]

        try:
            self.custom_horizontal_layout = py.horizontalLayout('custom_layout', p=self.search_column, ratios=[0, 0, 0])
        except RuntimeError:
            for i in xrange(0, len(self.custom_image_path_list)):
                py.deleteUI('custom_image_%i' % i)
        self.custom_image_path_list.append(path)
        self.custom_image_thumb_path_list.append(thumb_path)

        for i in xrange(0, len(self.custom_image_path_list)):
            image_name = 'custom_image_%i' % i
            py.image(image_name, p=self.custom_horizontal_layout, i=self.custom_image_thumb_path_list[i])

            image_menu = py.popupMenu(image_name+'_menu', p=image_name, ctl=False, button=3)

            py.menuItem('Pop out', p=image_menu, c=py.Callback(self.pop_out_gui, self.custom_image_path_list[i]))

            reference_submenu = py.menuItem('polyPlane Reference', p=image_menu, subMenu=True)
            for k in xrange(1, 4):
                view_submenu = py.menuItem(self.title_list[0][k], subMenu=True, p=reference_submenu)
                py.menuItem(self.title_list[1][k], p=view_submenu, c=py.Callback(df.reference_plane, False,
                                                                                      axis=k,
                                                                                      path=self.custom_image_path_list[i],
                                                                                      term='Custom_Image',
                                                                                      width=width,
                                                                                      height=height,
                                                                                      scaleFactor=0.5))
                py.menuItem(self.title_list[2][k], p=view_submenu, c=py.Callback(df.reference_plane, True,
                                                                                      axis=k,
                                                                                      path=self.custom_image_path_list[i],
                                                                                      term='Custom_Image',
                                                                                      width=width,
                                                                                      height=height,
                                                                                      scaleFactor=0.5))
            image_plane_submenu = py.menuItem('Image Plane Reference', p=image_menu, subMenu=True)

            py.menuItem('Create Image Plane', p=image_plane_submenu, c=py.Callback(df.image_plane,
                                                                                   self.custom_image_path_list[i],
                                                                                   widthHeight=image_attr_list[3]))

            py.menuItem('Apply as Texture', p=image_menu, c=py.Callback(df.apply_as_texture,
                                                                        path=self.custom_image_path_list[i],
                                                                        name=image_name))

            py.menuItem('Delete Image', p=image_menu, c=py.Callback(self.delete_image, image_name))

        self.custom_horizontal_layout.redistribute()

        return 0

    def delete_image(self, image_name):
        py.deleteUI(image_name)
        self.custom_horizontal_layout.redistribute()