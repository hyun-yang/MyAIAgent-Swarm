from functools import partial

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QSplitter, QComboBox, QLabel, QTabWidget, \
    QGroupBox, QFormLayout, QPushButton, QHBoxLayout, QApplication, QTextEdit, QSpinBox, QListWidget, \
    QCheckBox, QLineEdit

from chat.view.ChatHistory import ChatHistory
from chat.view.ChatWidget import ChatWidget
from custom.PromptTextEdit import PromptTextEdit
from util.ChatType import ChatType
from util.Constants import Constants
from util.Constants import ProviderName, UI
from util.SettingsManager import SettingsManager
from util.Utility import Utility


class ChatView(QWidget):
    submitted_signal = pyqtSignal(object)
    stop_signal = pyqtSignal()
    reload_chat_detail_signal = pyqtSignal(int)

    def __init__(self, model):
        super().__init__()
        self.model = model
        self._settings = SettingsManager.get_settings()
        self._current_chat_llm = Utility.get_settings_value(section="AI_Provider", prop="llm",
                                                            default="OpenAI", save=True)
        self.found_text_positions = []
        self.initialize_ui()

    def initialize_ui(self):

        # Top layout
        self.top_layout = QVBoxLayout()
        self.top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create buttons
        self.clear_all_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'bin.png')), UI.CLEAR_ALL)
        self.clear_all_button.clicked.connect(lambda: self.clear_all())

        self.copy_all_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'cards-stack.png')), UI.COPY_ALL)
        self.copy_all_button.clicked.connect(lambda: QApplication.clipboard().setText(self.get_all_text_content()))

        self.reload_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'cards-address.png')), UI.RELOAD_ALL)
        self.reload_button.clicked.connect(lambda: self.reload_chat_detail_signal.emit(-1))

        self.search_text = PromptTextEdit()
        self.search_text.submitted_signal.connect(self.search)
        self.search_text.setPlaceholderText(UI.SEARCH_PROMPT_PLACEHOLDER)

        self.search_text.setFixedHeight(self.clear_all_button.sizeHint().height())
        self.search_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.search_result = QLabel()

        # Create navigation buttons
        self.prev_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'arrow-180.png')), '')
        self.prev_button.clicked.connect(self.scroll_to_previous_match_widget)
        self.next_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'arrow.png')), '')
        self.next_button.clicked.connect(self.scroll_to_next_match_widget)

        # Create a horizontal layout and add the buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.search_text)
        button_layout.addWidget(self.search_result)
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.copy_all_button)
        button_layout.addWidget(self.clear_all_button)
        button_layout.addWidget(self.reload_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Add the button layout to the result layout
        self.top_layout.addLayout(button_layout)

        self.top_widget = QWidget()
        self.top_widget.setLayout(self.top_layout)
        self.top_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        # Result View
        self.result_layout = QVBoxLayout()
        self.result_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.result_layout.setSpacing(0)
        self.result_layout.setContentsMargins(0, 0, 0, 0)

        self.result_widget = QWidget()
        self.result_widget.setLayout(self.result_layout)

        # Scroll Area
        self.ai_answer_scroll_area = QScrollArea()
        self.ai_answer_scroll_area.setWidgetResizable(True)
        self.ai_answer_scroll_area.setWidget(self.result_widget)

        # Stop Button
        self.stop_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'minus-circle.png')), 'Stop')
        self.stop_button.clicked.connect(self.force_stop)

        stop_layout = QHBoxLayout()
        stop_layout.setContentsMargins(0, 0, 0, 0)
        stop_layout.setSpacing(0)
        stop_layout.addWidget(self.stop_button)
        stop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stop_widget = QWidget()
        self.stop_widget.setLayout(stop_layout)
        self.stop_widget.setVisible(False)

        # Prompt View
        self.prompt_text = PromptTextEdit()
        self.prompt_text.submitted_signal.connect(partial(self.handle_submitted_signal, name=ProviderName.TAVILY.value))
        self.prompt_text.setPlaceholderText(UI.CHAT_PROMPT_PLACEHOLDER)

        prompt_layout = QVBoxLayout()
        prompt_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        prompt_layout.addWidget(self.prompt_text)
        prompt_layout.setSpacing(0)
        prompt_layout.setContentsMargins(0, 0, 0, 0)

        self.prompt_widget = QWidget()
        self.prompt_widget.setLayout(prompt_layout)
        self.prompt_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        chat_layout = QVBoxLayout()

        chat_layout.addWidget(self.top_widget)
        chat_layout.addWidget(self.ai_answer_scroll_area)
        chat_layout.addWidget(self.stop_widget)
        chat_layout.addWidget(self.prompt_widget)

        chatWidget = QWidget()
        chatWidget.setLayout(chat_layout)

        config_layout = QVBoxLayout()

        self.config_tabs = QTabWidget()
        chat_icon = QIcon(Utility.get_icon_path('ico', 'processor.png'))
        self.config_tabs.addTab(self.create_parameters_tab(), chat_icon, UI.AI_AGENT)
        self.config_tabs.addTab(self.create_chatdb_tab(), chat_icon, UI.AI_AGENT_QA_LIST)

        config_layout.addWidget(self.config_tabs)

        configWidget = QWidget()
        configWidget.setLayout(config_layout)

        mainWidget = QSplitter(Qt.Orientation.Horizontal)
        mainWidget.addWidget(configWidget)
        mainWidget.addWidget(chatWidget)
        mainWidget.setSizes([UI.QSPLITTER_LEFT_WIDTH, UI.QSPLITTER_RIGHT_WIDTH])
        mainWidget.setHandleWidth(UI.QSPLITTER_HANDLEWIDTH)

        main_layout = QVBoxLayout()
        main_layout.addWidget(mainWidget)

        self.setLayout(main_layout)

    def reset_search_bar(self):
        self.found_text_positions = []
        self.search_result.clear()
        self.current_position_index = -1
        self.update_navigation_buttons()

    def search(self, text: str):
        if text and text.strip() and len(text) >= 2:
            self.found_text_positions = []
            self.current_position_index = -1

            search_text_lower = text.lower()

            for i in range(self.result_layout.count()):
                current_widget = self.result_layout.itemAt(i).widget()
                current_text = current_widget.get_original_text()
                current_text_lower = current_text.lower()

                if search_text_lower in current_text_lower:
                    self.found_text_positions.append(i)
                    highlight_text = current_widget.highlight_search_text(current_text, text)
                    current_widget.apply_highlight(highlight_text)
                else:
                    current_widget.show_original_text()

            if self.found_text_positions:
                self.current_position_index = 0
                self.scroll_to_match_widget(self.found_text_positions[self.current_position_index])
        if len(self.found_text_positions) > 0:
            self.search_result.setText(f'{len(self.found_text_positions)} {UI.FOUNDS}')
        else:
            self.search_result.clear()
        self.update_navigation_buttons()
        self.search_text.clear()

    def scroll_to_match_widget(self, position):
        self.ai_answer_scroll_area.ensureWidgetVisible(self.result_layout.itemAt(position).widget())

    def scroll_to_previous_match_widget(self):
        if len(self.found_text_positions) > 0 and self.current_position_index > 0:
            self.current_position_index -= 1
            self.scroll_to_match_widget(self.found_text_positions[self.current_position_index])
            self.update_navigation_buttons()

    def scroll_to_next_match_widget(self):
        if len(self.found_text_positions) > 0 and self.current_position_index < len(self.found_text_positions) - 1:
            self.current_position_index += 1
            self.scroll_to_match_widget(self.found_text_positions[self.current_position_index])
            self.update_navigation_buttons()

    def update_navigation_buttons(self):
        self.prev_button.setEnabled(self.current_position_index > 0)
        self.next_button.setEnabled(self.current_position_index < len(self.found_text_positions) - 1)

    def create_parameters_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_openai_tabcontent(ProviderName.TAVILY.value), "Swarm")
        self.tabs.addTab(self.create_prompt_tabcontent("OrchestratorAgent"), "Orchestrator")
        self.tabs.addTab(self.create_prompt_tabcontent("ProgrammerAgent"), "Programmer")
        self.tabs.addTab(self.create_prompt_tabcontent("TesterAgent"), "Tester")
        self.tabs.addTab(self.create_prompt_tabcontent("SearchAgent"), "Search")

        layout.addWidget(self.tabs)
        layoutWidget.setLayout(layout)
        return layoutWidget

    def set_default_tab(self, name):
        index = self.tabs.indexOf(self.tabs.findChild(QWidget, name))
        if index != -1:
            self.tabs.setCurrentIndex(index)

    def on_prompt_change(self, name):
        current_text = self.findChild(QComboBox, f"{name}_promptList").currentText()
        prompt_values = Utility.get_system_value(section=f"{name}_Prompt", prefix="prompt",
                                                 default="You are a helpful assistant.", length=3)
        current_prompt = self.findChild(QTextEdit, f"{name}_current_prompt")
        if current_text in prompt_values:
            current_prompt.setText(prompt_values[current_text])
        else:
            current_prompt.clear()

    def save_prompt_value(self, name):
        current_promptList = self.findChild(QComboBox, f"{name}_promptList")
        current_prompt = self.findChild(QTextEdit, f"{name}_current_prompt")
        selected_key = current_promptList.currentText()
        value = current_prompt.toPlainText()
        self._settings.setValue(f"{name}_Prompt/{selected_key}", value)
        self.update_prompt_list(name, Utility.extract_number_from_end(selected_key) - 1)

    def update_prompt_list(self, name, index=0):
        current_promptList = self.findChild(QComboBox, f"{name}_promptList")
        prompt_values = Utility.get_system_value(section=f"{name}_Prompt", prefix="prompt",
                                                 default="You are a helpful assistant.", length=3)
        if current_promptList:
            current_promptList.clear()
            current_promptList.addItems(prompt_values.keys())

        if prompt_values and current_promptList:
            current_promptList.setCurrentIndex(index)

    def create_openai_tabcontent(self, name):
        tab_widget = QWidget()
        tab_widget.setObjectName(name)
        layout_main = QVBoxLayout()

        # Tavily Search Group
        tavily_search_group = QGroupBox("Tavily Search Parameters")
        tavily_search_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tavily_search_layout = QFormLayout()

        search_depth_ComboBox = QComboBox()
        search_depth_ComboBox.setObjectName(f"{name}_search_depth_comboBox")
        search_depth_ComboBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        search_depth_ComboBox.addItems(Constants.SEARCH_DEPTH_LIST)
        search_depth_ComboBox.setCurrentText(
            Utility.get_settings_value(section=f"{name}_Search_Parameter", prop="search_depth",
                                       default="advanced", save=True)
        )
        search_depth_ComboBox.currentTextChanged.connect(lambda value: self.search_depth_changed(value, name))
        tavily_search_layout.addRow('Search Depth', search_depth_ComboBox)

        topic_ComboBox = QComboBox()
        topic_ComboBox.setObjectName(f"{name}_topic_comboBox")
        topic_ComboBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        topic_ComboBox.addItems(Constants.TOPIC_LIST)
        current_topic = Utility.get_settings_value(section=f"{name}_Search_Parameter", prop="topic",
                                                   default="general", save=True)
        topic_ComboBox.setCurrentText(current_topic)
        topic_ComboBox.currentTextChanged.connect(lambda value: self.topic_changed(value, name))
        tavily_search_layout.addRow('Topic', topic_ComboBox)

        max_result_spinBox = QSpinBox()
        max_result_spinBox.setObjectName(f"{name}_max_result_spinBox")
        max_result_spinBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        max_result_spinBox.setRange(1, 100)
        max_result_spinBox.setAccelerated(True)
        max_result_spinBox.setSingleStep(1)
        max_result_spinBox.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Search_Parameter", prop="max_result",
                                           default="5", save=True)))
        max_result_spinBox.valueChanged.connect(lambda value: self.max_result_changed(value, name))
        tavily_search_layout.addRow('Max Result', max_result_spinBox)

        days_SpinBox = QSpinBox()
        days_SpinBox.setObjectName(f"{name}_days_spinBox")
        days_SpinBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        days_SpinBox.setRange(1, 3650)
        days_SpinBox.setAccelerated(True)
        days_SpinBox.setSingleStep(1)
        days_SpinBox.setValue(
            int(
                Utility.get_settings_value(section=f"{name}_Search_Parameter", prop="days",
                                           default="365", save=True)))
        days_SpinBox.valueChanged.connect(lambda value: self.days_changed(value, name))
        # Set initial state
        days_SpinBox.setEnabled(current_topic == "news")
        tavily_search_layout.addRow('Days', days_SpinBox)

        # The days_SpinBox only get enabled when topic_ComboBox value is 'news'
        topic_ComboBox.currentTextChanged.connect(
            lambda value: days_SpinBox.setEnabled(value == "news")
        )

        include_answer_checkbox = QCheckBox("Include Answers")
        include_answer_checkbox.setObjectName(f"{name}_include_answer_checkbox")
        include_answer_checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        include_answer_checkbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Search_Parameter", prop="include_answer", default="False",
                                        save=True)) == "True")
        include_answer_checkbox.toggled.connect(lambda value: self.include_answer_changed(value, name))
        tavily_search_layout.addWidget(include_answer_checkbox)

        include_raw_content_checkbox = QCheckBox("Include Raw Content")
        include_raw_content_checkbox.setObjectName(f"{name}_include_raw_content_checkbox")
        include_raw_content_checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        include_raw_content_checkbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Search_Parameter", prop="include_raw_content", default="True",
                                        save=True)) == "True")
        include_raw_content_checkbox.toggled.connect(lambda value: self.include_raw_content_changed(value, name))
        tavily_search_layout.addWidget(include_raw_content_checkbox)

        include_images_checkbox = QCheckBox("Include Images")
        include_images_checkbox.setObjectName(f"{name}_include_images_checkbox")
        include_images_checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        include_images_checkbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Search_Parameter", prop="include_images", default="False",
                                        save=True)) == "True")
        include_images_checkbox.toggled.connect(lambda value: self.include_images_changed(value, name))
        tavily_search_layout.addWidget(include_images_checkbox)

        tavily_search_group.setLayout(tavily_search_layout)
        layout_main.addWidget(tavily_search_group)

        # Include Domain List Group
        include_domain_list_group = QGroupBox("Tavily Search Include Domain List")
        include_domain_list_layout = QVBoxLayout()
        include_domain_list_group.setLayout(include_domain_list_layout)

        # Include Domain Line Edit
        include_domain_layout = QHBoxLayout()
        include_domain_line_edit = QLineEdit()
        include_domain_line_edit.setObjectName(f"{name}_include_domain_line_edit")
        include_domain_line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        include_domain_line_edit.setPlaceholderText('Add domain name you want to include')
        include_domain_layout.addWidget(include_domain_line_edit)

        include_add_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'plus.png')), "Add")
        include_add_button.setObjectName(f"{name}_IncludeAddButton")
        include_domain_layout.addWidget(include_add_button)

        include_domain_list_layout.addLayout(include_domain_layout)

        # Add QListWidget to show include domain list
        include_domain_list_widget = QListWidget()
        include_domain_list_widget.setObjectName(f"{name}_IncludeDomainList")
        include_domain_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        include_domain_list_layout.addWidget(include_domain_list_widget)

        # Load include domains from settings.ini
        self.load_domains_from_settings(include_domain_list_widget, 'Include')

        # Add buttons
        include_buttons_layout = QHBoxLayout()

        include_delete_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'minus.png')), "Remove")
        include_delete_button.setObjectName(f"{name}_IncludeDeleteButton")
        include_delete_button.setEnabled(False)
        include_buttons_layout.addWidget(include_delete_button)

        include_domain_list_layout.addLayout(include_buttons_layout)
        layout_main.addWidget(include_domain_list_group)

        include_add_button.clicked.connect(
            lambda: self.add_domain_to_list(include_domain_line_edit, include_domain_list_widget))
        include_domain_line_edit.returnPressed.connect(
            lambda: self.add_domain_to_list(include_domain_line_edit, include_domain_list_widget))
        include_domain_list_widget.itemSelectionChanged.connect(
            lambda: self.toggle_delete_button(include_domain_list_widget, include_delete_button))
        include_delete_button.clicked.connect(lambda: self.remove_selected_domain(include_domain_list_widget))

        # Exclude Domain List Group
        exclude_domain_list_group = QGroupBox("Tavily Search Exclude Domain List")
        exlude_domain_list_layout = QVBoxLayout()
        exclude_domain_list_group.setLayout(exlude_domain_list_layout)

        # Exclude Domain Line Edit
        exclude_domain_layout = QHBoxLayout()
        exclude_domain_line_edit = QLineEdit()
        exclude_domain_line_edit.setObjectName(f"{name}_exclude_domain_line_edit")
        exclude_domain_line_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        exclude_domain_line_edit.setPlaceholderText('Add domain name you want to exclude')
        exclude_domain_layout.addWidget(exclude_domain_line_edit)

        exclude_add_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'plus.png')), "Add")
        exclude_add_button.setObjectName(f"{name}_ExcludeAddButton")
        exclude_domain_layout.addWidget(exclude_add_button)

        exlude_domain_list_layout.addLayout(exclude_domain_layout)

        # Add QListWidget to show exclude domain list
        exclude_domain_list_widget = QListWidget()
        exclude_domain_list_widget.setObjectName(f"{name}_ExcludeDomainList")
        exclude_domain_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        exlude_domain_list_layout.addWidget(exclude_domain_list_widget)

        # Load exclude domains from settings
        self.load_domains_from_settings(exclude_domain_list_widget, 'Exclude')

        # Add buttons
        exclude_buttons_layout = QHBoxLayout()

        exclude_delete_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'minus.png')), "Remove")
        exclude_delete_button.setObjectName(f"{name}_ExcludeDeleteButton")
        exclude_delete_button.setEnabled(False)
        exclude_buttons_layout.addWidget(exclude_delete_button)

        exlude_domain_list_layout.addLayout(exclude_buttons_layout)
        layout_main.addWidget(exclude_domain_list_group)

        exclude_add_button.clicked.connect(
            lambda: self.add_domain_to_list(exclude_domain_line_edit, exclude_domain_list_widget))
        exclude_domain_line_edit.returnPressed.connect(
            lambda: self.add_domain_to_list(exclude_domain_line_edit, exclude_domain_list_widget))
        exclude_domain_list_widget.itemSelectionChanged.connect(
            lambda: self.toggle_delete_button(exclude_domain_list_widget, exclude_delete_button))
        exclude_delete_button.clicked.connect(lambda: self.remove_selected_domain(exclude_domain_list_widget))

        # Stream Option
        option_group = QGroupBox("OpenAI Options")
        option_layout = QVBoxLayout()

        streamCheckbox = QCheckBox("Stream")
        streamCheckbox.setObjectName(f"{name}_streamCheckbox")
        streamCheckbox.setChecked(
            (Utility.get_settings_value(section=f"{name}_Search_Parameter", prop="stream", default="True",
                                        save=True)) == "True")
        streamCheckbox.toggled.connect(lambda value: self.stream_changed(value, name))
        option_layout.addWidget(streamCheckbox)
        option_group.setLayout(option_layout)
        layout_main.addWidget(option_group)

        tab_widget.setLayout(layout_main)

        return tab_widget

    def load_domains_from_settings(self, list_widget, domain_type):
        settings = SettingsManager.get_settings()
        settings.beginGroup(f"Tavily_{domain_type}_Domain_List")

        keys = settings.allKeys()
        for key in keys:
            if settings.value(key, type=bool):
                list_widget.addItem(key)

        settings.endGroup()

    def add_domain_to_list(self, domain_line_edit, domain_list_widget):
        domain = domain_line_edit.text().strip()
        if domain:
            domain_list_widget.addItem(domain)
            domain_line_edit.clear()
            if domain_list_widget.objectName() == "Tavily_IncludeDomainList":
                include_domain_list = self.get_include_domain_list(ProviderName.TAVILY.value)
                Utility.add_tavily_model_list(include_domain_list, 'Include')
            elif domain_list_widget.objectName() == "Tavily_ExcludeDomainList":
                exclude_domain_list = self.get_exclude_domain_list(ProviderName.TAVILY.value)
                Utility.add_tavily_model_list(exclude_domain_list, 'Exclude')

    def remove_selected_domain(self, domain_list_widget):
        for item in domain_list_widget.selectedItems():
            domain = item.text()
            domain_list_widget.takeItem(domain_list_widget.row(item))

            if domain_list_widget.objectName() == "Tavily_IncludeDomainList":
                domain_type = 'Include'
            elif domain_list_widget.objectName() == "Tavily_ExcludeDomainList":
                domain_type = 'Exclude'
            else:
                continue

            Utility.remove_tavily_model_list(domain, domain_type)

    def toggle_delete_button(self, domain_list_widget, delete_button):
        delete_button.setEnabled(bool(domain_list_widget.selectedItems()))

    def create_prompt_tabcontent(self, name):
        tabWidget = QWidget()
        tabWidget.setObjectName(name)
        layoutMain = QVBoxLayout()

        groupSystem = self.create_prompt_layout(name)
        layoutMain.addWidget(groupSystem)

        tabWidget.setLayout(layoutMain)

        return tabWidget

    def max_result_changed(self, value, name):
        self._settings.setValue(f"{name}_Search_Parameter/max_result", value)

    def days_changed(self, value, name):
        self._settings.setValue(f"{name}_Search_Parameter/days", value)

    def search_depth_changed(self, value, name):
        self._settings.setValue(f"{name}_Search_Parameter/search_depth", value)

    def topic_changed(self, value, name):
        self._settings.setValue(f"{name}_Search_Parameter/topic", value)

    def stream_changed(self, checked, name):
        if checked:
            self._settings.setValue(f"{name}_Search_Parameter/stream", 'True')
        else:
            self._settings.setValue(f"{name}_Search_Parameter/stream", 'False')

    def include_answer_changed(self, checked, name):
        if checked:
            self._settings.setValue(f"{name}_Search_Parameter/include_answer", 'True')
        else:
            self._settings.setValue(f"{name}_Search_Parameter/include_answer", 'False')

    def include_raw_content_changed(self, checked, name):
        if checked:
            self._settings.setValue(f"{name}_Search_Parameter/include_raw_content", 'True')
        else:
            self._settings.setValue(f"{name}_Search_Parameter/include_raw_content", 'False')

    def include_images_changed(self, checked, name):
        if checked:
            self._settings.setValue(f"{name}_Search_Parameter/include_images", 'True')
        else:
            self._settings.setValue(f"{name}_Search_Parameter/include_images", 'False')

    def create_prompt_layout(self, name):
        groupSystem = QGroupBox(f"{name} Prompt")

        promptLayout = QFormLayout()
        promptLabel = QLabel("Select Prompt")
        promptList = QComboBox()
        promptList.setObjectName(f"{name}_promptList")
        prompt_values = Utility.get_system_value(section=f"{name}_Prompt", prefix="prompt",
                                                 default="You are a helpful assistant.", length=3)
        promptList.addItems(prompt_values.keys())
        promptList.currentIndexChanged.connect(lambda: self.on_prompt_change(name))

        current_prompt = QTextEdit()
        current_prompt.setObjectName(f"{name}_current_prompt")
        current_prompt.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        current_prompt.setMinimumHeight(150)
        current_prompt.setText(prompt_values['prompt1'])

        save_prompt_button = QPushButton(QIcon(Utility.get_icon_path('ico', 'disk-black.png')), 'Save')
        save_prompt_button.clicked.connect(lambda: self.save_prompt_value(name))

        promptLayout.addRow(promptLabel)
        promptLayout.addRow(promptList)
        promptLayout.addRow(current_prompt)
        promptLayout.addRow(save_prompt_button)

        groupSystem.setLayout(promptLayout)

        return groupSystem

    def create_chatdb_tab(self):
        layoutWidget = QWidget()
        layout = QVBoxLayout()

        self._chat_history = ChatHistory(self.model)

        layout.addWidget(self._chat_history)

        layoutWidget.setLayout(layout)
        return layoutWidget

    def update_ui_submit(self, chatType, text):
        self.ai_answer_scroll_area.verticalScrollBar().rangeChanged.connect(self.adjust_scroll_bar)
        self.add_user_question(chatType, text)
        self.stop_widget.setVisible(True)

    def add_user_question(self, chatType, text):
        user_question = ChatWidget(chatType, text)
        self.result_layout.addWidget(user_question)

    def adjust_scroll_bar(self, min_val, max_val):
        self.ai_answer_scroll_area.verticalScrollBar().setSliderPosition(max_val)

    def update_ui(self, result, stream):
        if stream:
            chatWidget = self.get_last_ai_widget()

            if chatWidget:
                chatWidget.add_text(result)
            else:
                chatWidget = ChatWidget(ChatType.AI)
                chatWidget.add_text(result)
                self.result_layout.addWidget(chatWidget)

        else:
            ai_answer = ChatWidget(ChatType.AI, result)
            self.result_layout.addWidget(ai_answer)

    def update_ui_finish(self, model, finish_reason, elapsed_time, stream):
        self.ai_answer_scroll_area.verticalScrollBar().rangeChanged.disconnect()
        chatWidget = self.get_last_ai_widget()
        if stream:
            if chatWidget:
                chatWidget.apply_style()
                self.stop_widget.setVisible(False)
        else:
            self.stop_widget.setVisible(False)

        if chatWidget and chatWidget.get_chat_type() == ChatType.AI:
            chatWidget.set_model_name(
                Constants.MODEL_PREFIX + model + Constants.RESPONSE_TIME + format(elapsed_time, ".2f"))

    def get_last_ai_widget(self) -> ChatWidget | None:
        layout_item = self.result_widget.layout().itemAt(self.result_widget.layout().count() - 1)
        if layout_item:
            last_ai_widget = layout_item.widget()
            if last_ai_widget.get_chat_type() == ChatType.AI:
                return last_ai_widget
        else:
            return None

    def get_agent_prompts(self):

        orchestrator_agent_prompt = self.findChild(QTextEdit, 'OrchestratorAgent_current_prompt').toPlainText()
        programmer_agent_prompt = self.findChild(QTextEdit, 'ProgrammerAgent_current_prompt').toPlainText()
        tester_agent_prompt = self.findChild(QTextEdit, 'TesterAgent_current_prompt').toPlainText()
        search_agent_prompt = self.findChild(QTextEdit, 'SearchAgent_current_prompt').toPlainText()

        agent_prompts = {
            "orchestrator_agent": {
                "name": "Orchestrator Agent",
                "instructions": orchestrator_agent_prompt
            },
            "search_agent": {
                "name": "Search Agent",
                "instructions": search_agent_prompt
            },
            "programmer_agent": {
                "name": "Programmer Agent",
                "instructions": programmer_agent_prompt
            },
            "tester_agent": {
                "name": "Tester Agent",
                "instructions": tester_agent_prompt
            },
        }
        return agent_prompts

    def get_include_domain_list(self, name):
        domain_name_list = self.findChild(QListWidget, f"{name}_IncludeDomainList")
        if domain_name_list.count():
            return [domain_name_list.item(i).text() for i in range(domain_name_list.count())]
        return None

    def get_exclude_domain_list(self, name):
        domain_name_list = self.findChild(QListWidget, f"{name}_ExcludeDomainList")
        if domain_name_list.count():
            return [domain_name_list.item(i).text() for i in range(domain_name_list.count())]
        return None

    def handle_submitted_signal(self, text, name):
        if text:
            search_tool_args = {
                'name': 'Tavily',
                'query': text,
                'tavily_api_key': self._settings.value(f'AI_Provider/Tavily'),
                'search_depth': self.findChild(QComboBox,
                                               f'{name}_search_depth_comboBox').currentText(),
                'topic': self.findChild(QComboBox, f'{name}_topic_comboBox').currentText(),
                'max_results': self.findChild(QSpinBox, f'{name}_max_result_spinBox').value(),
                'days': self.findChild(QSpinBox, f'{name}_days_spinBox').value(),
                'include_answer': self.findChild(QCheckBox,
                                                 f'{name}_include_answer_checkbox').isChecked(),
                'include_raw_content': self.findChild(QCheckBox,
                                                      f'{name}_include_raw_content_checkbox').isChecked(),
                'include_images': self.findChild(QCheckBox,
                                                 f'{name}_include_images_checkbox').isChecked(),
                'include_domains': self.get_include_domain_list(name),
                'exclude_domains': self.get_exclude_domain_list(name),
            }

            all_messages = self.get_all_text()
            all_messages.append({"role": "user", "content": text})
            args = {
                'open_api_key': self._settings.value(f'AI_Provider/OpenAI'),
                'messages': all_messages,
                'agent_prompt_list': self.get_agent_prompts(),
                'search_tool_args': search_tool_args,
                'stream': self.findChild(QCheckBox, f'{name}_streamCheckbox').isChecked()
            }
            self.submitted_signal.emit(args)

    def start_chat(self):
        self.prompt_text.clear()
        self.prompt_text.setEnabled(False)

    def finish_chat(self):
        self.prompt_text.setEnabled(True)
        self.prompt_text.setFocus()

    def get_all_text_content(self):
        all_previous_qa = self.get_all_text()
        return '\n'.join(qa["content"] for qa in all_previous_qa)

    def get_all_text(self):
        all_previous_qa = []
        for i in range(self.result_layout.count()):
            current_widget = self.result_layout.itemAt(i).widget()
            if current_widget.get_chat_type() == ChatType.HUMAN and len(current_widget.get_text()) > 0:
                all_previous_qa.append({"role": "user", "content": current_widget.get_text()})
            elif current_widget.get_chat_type() == ChatType.AI and len(current_widget.get_text()) > 0:
                all_previous_qa.append({"role": "assistant", "content": current_widget.get_text()})
        return all_previous_qa

    def clear_all(self):
        target_layout = self.result_layout
        if target_layout is not None:
            while target_layout.count():
                item = target_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

    def force_stop(self):
        self.stop_signal.emit()
        self.stop_widget.setVisible(False)

    @property
    def chat_history(self):
        return self._chat_history
