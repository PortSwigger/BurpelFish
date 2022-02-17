#!/usr/bin/python

# If you want to hardcode your Google Cloud Translation API key - initialise the key variable with it:
# key = 'YOUR_API_KEY'
key = ''

# BurpelFish
# Copyright (c) 2018 Paul Taylor @bao7uo

#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

import inspect
import json
from java.awt.event import MouseAdapter
from java.awt.datatransfer import DataFlavor, StringSelection
from java.awt import Desktop, Toolkit
from java.net import URL, URI
from thread import start_new_thread
from javax.swing import JMenu, JMenuItem, JCheckBoxMenuItem, JOptionPane, JLabel
from burp import IBurpExtender, IHttpRequestResponse, IResponseInfo, IContextMenuFactory, IContextMenuInvocation

# Some languages have been removed to reduce the size of the menu. If your language isn't one of the defaults it is only because I personally probably won't use it any time soon. Please feel free to enable it for your self :-)

langs = {
    # 'Afrikaans': 'af',
    # 'Albanian': 'sq',
    'Arabic': 'ar',
    # 'Azerbaijani': 'az',
    # 'Basque': 'eu',
    # 'Belarusian': 'be',
    # 'Bengali': 'bn',
    # 'Bulgarian': 'bg',
    # 'Catalan': 'ca',
    'Chinese Simplified': 'zh-CN',
    'Chinese Traditional': 'zh-TW',
    # 'Croatian': 'hr',
    # 'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'English': 'en',
    # 'Esperanto': 'eo',
    # 'Estonian': 'et',
    # 'Filipino': 'tl',
    'Finnish': 'fi',
    'French': 'fr',
    # 'Galician': 'gl',
    # 'Georgian': 'ka',
    'German': 'de',
    'Greek': 'el',
    # 'Gujarati': 'gu',
    # 'Haitian Creole': 'ht',
    'Hebrew': 'iw',
    # 'Hindi': 'hi',
    # 'Hungarian': 'hu',
    'Icelandic': 'is',
    # 'Indonesian': 'id',
    # 'Irish': 'ga',
    'Italian': 'it',
    'Japanese': 'ja',
    # 'Kannada': 'kn',
    'Korean': 'ko',
    # 'Latin': 'la',
    # 'Latvian': 'lv',
    # 'Lithuanian': 'lt',
    # 'Macedonian': 'mk',
    # 'Malay': 'ms',
    # 'Maltese': 'mt',
    'Norwegian': 'no',
    # 'Persian': 'fa',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Romanian': 'ro',
    'Russian': 'ru',
    # 'Serbian': 'sr',
    # 'Slovak': 'sk',
    # 'Slovenian': 'sl',
    'Spanish': 'es',
    # 'Swahili': 'sw',
    'Swedish': 'sv',
    # 'Tamil': 'ta',
    # 'Telugu': 'te',
    'Thai': 'th',
    'Turkish': 'tr',
    # 'Ukrainian': 'uk',
    'Urdu': 'ur'
    # 'Vietnamese': 'vi',
    # 'Welsh': 'cy',
    # 'Yiddish': 'yi'
}


def get_script_dir(follow_symlinks=True):

    if getattr(sys, 'frozen', False):  # py2exe, PyInstaller, cx_Freeze
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)


def translate(query, src, dst):

    global key

    if src == 'Automatic':
        src = 'auto'
    else:
        src = langs.get(src)
    dst = langs.get(dst)

    query = cb.helpers.urlEncode(query)

    if key == '':
        key = JOptionPane.showInputDialog(
            'Please enter a valid Google Cloud Translation API key to continue.\n'
            'See the source code for details of how the key can be hardcoded.\n\n'
            'If you wish to use this extension without an API key, just click OK.'
        )
    if key == "" or key == "GoogleTranslateAPI":
        # -- Google Translate API
        key = "GoogleTranslateAPI"
        host = 'translate.googleapis.com'
        path = 'translate_a/single'
        params = 'client=gtx&dt=t&ie=UTF-8&oe=UTF-8&sl=%s&tl=%s&q=%s' % (
            src, dst, query)

        def result(r): return r[0][0][0]

        def result_src(r): return r[2]
    # -- End Google Translate API
    else:
        # -- Google Cloud Translation API
        if src == 'auto':
            src = ''
        params = 'format=text&source=%s&target=%s&q=%s&key=%s' % (
            src, dst, query, key)
        host = 'translation.googleapis.com'
        path = 'language/translate/v2'

        def result(r): return r['data']['translations'][0]['translatedText']
        if src == '':
            def result_src(
                r): return r['data']['translations'][0]['detectedSourceLanguage']
        else:
            def result_src(r): return src
    # -- End Google Cloud Translation API

    url = URL('https://%s/%s?%s' % (host, path, params))
    request = cb.helpers.buildHttpRequest(url)
    request = cb.helpers.toggleRequestMethod(request)
    service = cb.helpers.buildHttpService(host, 443, 'https')
    requested = cb.callbacks.makeHttpRequest(service, request)
    response = cb.helpers.bytesToString(requested.getResponse())
    info = cb.helpers.analyzeResponse(response)
    body = response[info.getBodyOffset():]
    data = json.loads(body)

    return(result(data), next(key for key, value in langs.items() if value == result_src(data)))


class mouseAdapter(MouseAdapter):

    def mouseClicked(self, msg):
        Desktop.getDesktop().browse(URI("https://translate.google.com"))


def popup_translate(control, query, src, dst, message, selection, text, context, invoker, from_clipboard):

    editor = False

    result, result_src = translate(query, src, dst)
    cb.callbacks.printOutput('[%s] %s --> [%s] %s' % (result_src, query.decode(
        'utf-8', 'strict'), dst, result.decode('utf-8', 'strict')))

    if (context == invoker.CONTEXT_MESSAGE_EDITOR_REQUEST or
            context == invoker.CONTEXT_MESSAGE_EDITOR_RESPONSE
        ) and from_clipboard == False:
        editor = True
        buttons = ['Replace Original', 'Copy to Clipboard', 'OK']
    else:
        buttons = ['Copy to Clipboard', 'OK']
    label = JLabel('<html>%s to %s:<br><br><b>%s</b><br><br><img border=0 src="file:///%s/color-short.png"></html>' %
                   (result_src, dst, result.decode('utf-8', 'strict'), get_script_dir()))
    label.putClientProperty("html.disable", None)

    label.addMouseListener(mouseAdapter())

    popup_result = JOptionPane.showOptionDialog(control, label, '%s' % (
        BurpExtender.extension_name), 0, JOptionPane.PLAIN_MESSAGE, None, buttons, None)
    if (editor is True and popup_result == 1) or (editor is False and popup_result == 0):
        clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
        clipboard.setContents(StringSelection(result), None)
    elif (editor is True and popup_result == 0):
        if context == invoker.CONTEXT_MESSAGE_EDITOR_REQUEST:
            setter = message.setRequest
        else:
            setter = message.setResponse
        setter(cb.helpers.stringToBytes(
            text[:selection[0]] + result + text[selection[1]:]))


class cb():

    callbacks = None

    def __init__(self, callbacks):

        cb.callbacks = callbacks
        cb.helpers = callbacks.getHelpers()


class MenuFactory(IContextMenuFactory):

    message = None
    selection = None
    bytes = None
    src = 'Automatic'
    dst = 'English'
    src_menu_text = 'Translate with Google (Current selection)'
    dst_menu_text = 'Translate with Google (Clipboard contents)'

    def get_clipboard_text(self):

        clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
        clipboard_text = None
        clipboard_contents = clipboard.getContents(self)
        if clipboard_contents.isDataFlavorSupported(DataFlavor.stringFlavor):
            clipboard_text = clipboard_contents.getTransferData(
                DataFlavor.stringFlavor)
        return clipboard_text

    def translate(self, message):

        http_request_response = self.invoker.getSelectedMessages()[0]

        context = self.invoker.getInvocationContext()
        if (context == self.invoker.CONTEXT_MESSAGE_EDITOR_REQUEST or
                context == self.invoker.CONTEXT_MESSAGE_VIEWER_REQUEST
            ):
            message_bytes = http_request_response.getRequest()
        else:
            message_bytes = http_request_response.getResponse()

        text = cb.helpers.bytesToString(message_bytes)

        from_clipboard = False

        if message.getSource().getText() == self.src_menu_text:
            query = text[self.selection[0]:self.selection[1]]
        else:
            query = self.get_clipboard_text()
            from_clipboard = True
        if query is not None:
            start_new_thread(popup_translate, (message.getSource().parent, query, self.src, self.dst,
                                               http_request_response, self.selection, text, context, self.invoker, from_clipboard))

    def select_src(self, message):

        self.src = message.getSource().getText()

    def select_dst(self, message):

        self.dst = message.getSource().getText()

    def createMenuItems(self, invoker):

        self.invoker = invoker

        self.selection = self.invoker.getSelectionBounds()

        context = self.invoker.getInvocationContext()
        if not (context == self.invoker.CONTEXT_MESSAGE_EDITOR_REQUEST or
                context == self.invoker.CONTEXT_MESSAGE_VIEWER_REQUEST or
                context == self.invoker.CONTEXT_MESSAGE_EDITOR_RESPONSE or
                context == self.invoker.CONTEXT_MESSAGE_VIEWER_RESPONSE
                ):
            return None

        menu_translate_sel = JMenuItem(
            self.src_menu_text, actionPerformed=self.translate)
        menu_translate_sel.setEnabled(False)
        menu_translate_clip = JMenuItem(
            self.dst_menu_text, actionPerformed=self.translate)
        menu_translate_clip.setEnabled(False)

        if self.selection is not None and self.selection[0] != self.selection[1]:
            menu_translate_sel.setEnabled(True)
        if self.get_clipboard_text() is not None:
            menu_translate_clip.setEnabled(True)

        menu_header = JMenu('%s v%s' % (
            BurpExtender.extension_name, BurpExtender.extension_version))
        menu_src = JMenu('Source Language [%s]' % (self.src))
        menu_dst = JMenu('Destination Language [%s]' % (self.dst))
        menu_automatic = JCheckBoxMenuItem(
            'Automatic', actionPerformed=self.select_src)
        menu_src.add(menu_automatic)
        if self.src == menu_automatic.getText():
            menu_automatic.setSelected(True)
        for lang in sorted(langs):
            menu_item = JCheckBoxMenuItem(
                lang, actionPerformed=self.select_src)
            if lang == self.src:
                menu_item.setSelected(True)
            menu_src.add(menu_item)
            menu_item = JCheckBoxMenuItem(
                lang, actionPerformed=self.select_dst)
            if lang == self.dst:
                menu_item.setSelected(True)
            menu_dst.add(menu_item)

        menu_header.add(menu_src)
        menu_header.add(menu_dst)
        menu_header.add(menu_translate_sel)
        menu_header.add(menu_translate_clip)

        return [menu_header]


class BurpExtender(IBurpExtender):

    extension_name = 'BurpelFish by @bao7uo'
    extension_version = '0.04'

    def registerExtenderCallbacks(self, callbacks):

        cb(callbacks)
        cb.callbacks.setExtensionName(self.extension_name)

        cb.callbacks.registerContextMenuFactory(MenuFactory())

        cb.callbacks.printOutput('%s v%s extension loaded' % (
            self.extension_name, self.extension_version))
        cb.callbacks.printOutput('\nTHIS SERVICE MAY CONTAIN TRANSLATIONS POWERED BY GOOGLE. GOOGLE DISCLAIMS ALL WARRANTIES RELATED TO THE TRANSLATIONS, EXPRESS OR IMPLIED, INCLUDING ANY WARRANTIES OF ACCURACY, RELIABILITY, AND ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.\n')
