APP_STYLE = """
QMainWindow {
  background: #f5eef1;
}

QWidget {
  color: #2f2830;
  font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
  font-size: 13px;
}

#RootFrame {
  background: #fffafa;
  border-left: 8px solid #d83a45;
  border-right: 8px solid #f8f5f1;
  border-top: 2px solid #d9ac52;
  border-bottom: 2px solid #d9ac52;
}

#TopBar {
  background: rgba(255, 250, 250, 230);
  border: 1px solid #ead5c2;
  border-radius: 8px;
}

#ConversationPanel {
  background: #f8e8ec;
  border: 1px solid #eccfd6;
  border-radius: 8px;
}

#ChatPanel {
  background: #ffffff;
  border: 1px solid #ead4d7;
  border-radius: 8px;
}

#ChatWallpaper {
  background: transparent;
  border: 1px solid #f0dcda;
  border-radius: 8px;
}

#RightPanel {
  background: #fff8f3;
  border: 1px solid #ead4c3;
  border-radius: 8px;
}

#Title {
  color: #c82f3c;
  font-size: 22px;
  font-weight: 700;
}

#Subtitle {
  color: #7b6167;
  font-size: 12px;
}

#SectionTitle {
  color: #49353b;
  font-size: 14px;
  font-weight: 700;
}

#ConversationItem {
  background: #ffffff;
  border: 1px solid #efd5dc;
  border-radius: 8px;
  padding: 9px;
}

#ConversationItemActive {
  background: #fff6e8;
  border: 1px solid #d9ac52;
  border-radius: 8px;
  padding: 9px;
}

#StatusPill {
  background: #fff;
  border: 1px solid #ebd7cf;
  border-radius: 8px;
  color: #6b5358;
  padding: 6px 8px;
}

#GoldPill {
  background: #fff8e7;
  border: 1px solid #dbb35c;
  border-radius: 8px;
  color: #735326;
  padding: 6px 8px;
}

#SearchBox {
  background: #fff;
  border: 1px solid #e6cbd2;
  border-radius: 8px;
  color: #8a7378;
  padding: 8px 10px;
}

QPushButton {
  background: #d83a45;
  color: #ffffff;
  border: 0;
  border-radius: 8px;
  padding: 9px 14px;
  font-weight: 700;
}

QPushButton:hover {
  background: #be2f3a;
}

QPushButton:disabled {
  background: #d8b9bd;
}

QTextEdit {
  background: #fff;
  border: 1px solid #e5ced2;
  border-radius: 8px;
  padding: 8px;
  selection-background-color: #d83a45;
}

QScrollArea {
  border: 0;
  background: transparent;
}

QScrollArea > QWidget > QWidget {
  background: transparent;
}

QScrollBar:vertical {
  background: transparent;
  width: 10px;
}

QScrollBar::handle:vertical {
  background: #e7bdc3;
  border-radius: 5px;
}
"""


USER_BUBBLE_STYLE = """
background: #d83a45;
color: #ffffff;
border-radius: 10px;
padding: 10px 12px;
"""


ASSISTANT_BUBBLE_STYLE = """
background: rgba(255, 250, 245, 238);
color: #3f3035;
border: 1px solid #efd9c3;
border-radius: 10px;
padding: 10px 12px;
"""


SYSTEM_BUBBLE_STYLE = """
background: rgba(247, 241, 243, 225);
color: #77656a;
border: 1px dashed #d8c4c9;
border-radius: 10px;
padding: 7px 10px;
"""
