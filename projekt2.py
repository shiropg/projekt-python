import sys 
from PyQt5.QtWidgets import QApplication, QPushButton, QGraphicsView, QGraphicsScene, QMainWindow, QGraphicsItem, QLineEdit, QLabel, QDialog, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath, QPolygonF, QBrush, QFont
import pyqtgraph as pg

class Rura(QGraphicsItem):
    def __init__(self, punkty, grubosc=12, kolor=Qt.gray):
        super().__init__()
        self.punkty = [QPointF(float(p[0]), float(p[1])) for p in punkty]
        self.grubosc = grubosc
        self.kolor_rury = kolor
        self.kolor_cieczy = QColor(0, 180, 255)
        self.czy_plynie = False
        self.setZValue(-1)

    def ustaw_przeplyw(self, plynie):
        self.czy_plynie = plynie
        self.update()

    def boundingRect(self):
        if not self.punkty:
            return QRectF()
        
        poly = QPolygonF(self.punkty)
        rect = poly.boundingRect()
        margin = self.grubosc/2+2
        return rect.adjusted(-margin, -margin, margin, margin)

    def paint(self, painter, option, widget=None):   
        path = QPainterPath()
        if self.punkty:
            path.moveTo(self.punkty[0])
            for p in self.punkty[1:]:
                path.lineTo(p)

        pen_rura = QPen(self.kolor_rury, self.grubosc, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen_rura)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        if self.czy_plynie:
            pen_ciecz = QPen(self.kolor_cieczy, self.grubosc - 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_ciecz)
            painter.drawPath(path)


class Zbiornik(QGraphicsItem):
    def __init__(self, x, y, width=100, height=140, nazwa=""):
        super().__init__()
        self.rect = QRectF(x, y, width, height)
        self.nazwa = nazwa
        self.pojemnosc = 100.0
        self.aktualna_ilosc = 0.0
        self.temp_aktualna = 20.0
        self.grubosc_scianki = 2
        self.setZValue(1)

    def boundingRect(self):
        return self.rect.adjusted(-10, -30, 10, 10)
    
    def paint(self, painter, option, widget=None):
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        painter.drawRect(self.rect)

        poziom=0
        if self.pojemnosc > 0:
            poziom = self.aktualna_ilosc/self.pojemnosc 

        if poziom > 0:
            h_cieczy = (self.rect.height()-self.grubosc_scianki)*poziom
            y_start = (self.rect.y()+self.rect.height())-(self.grubosc_scianki/2)-h_cieczy
            r=min(255, max(0, int((self.temp_aktualna-20)*5)))
            b=255-r
            painter.setBrush(QColor(r, 0, b, 200))
            painter.setPen(Qt.NoPen)

            offset = self.grubosc_scianki/2
            rect_wody = QRectF(self.rect.x()+offset, y_start, self.rect.width()-self.grubosc_scianki, h_cieczy)
            painter.drawRect(rect_wody)

        pen=QPen(Qt.black, self.grubosc_scianki)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect)

        painter.setPen(Qt.black)
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(int(self.rect.x()), int(self.rect.y()-8), self.nazwa)

        if poziom > 0.05:
            painter.drawText(self.rect.center(), f"{int(poziom*100)}%")

class Pompa(QGraphicsItem):
    def __init__(self, x, y):
        super().__init__()
        self.setPos(x, y)
        self.dziala = False
        self.temp_aktualna = 20.0

        self.setAcceptHoverEvents(True)
        self.rect_top=QRectF(15, 0, 30, 20)
        self.rect_main = QRectF(0, 20, 60, 40)

    def boundingRect(self):
        return QRectF(0, 0, 60, 60)

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(Qt.black, 2))
        
        r = min(100, max(70, int(70 + (self.temp_aktualna - 20)))) 
        kolor_korpusu = QColor(r, 70, 70) 
        painter.setBrush(QBrush(kolor_korpusu))
        
        painter.drawRect(self.rect_top)
        painter.drawRect(self.rect_main)
        
        painter.setPen(QPen(Qt.white, 2))
        painter.drawLine(self.rect_main.topLeft(), self.rect_main.bottomRight())
        painter.drawLine(self.rect_main.bottomLeft(), self.rect_main.topRight())

        kolor_lampki = Qt.green if self.dziala else Qt.red
        painter.setBrush(QBrush(kolor_lampki))
        painter.setPen(QPen(Qt.black, 1))
        painter.drawEllipse(self.rect_top.center(), 6, 6)

        painter.setPen(Qt.black)
        painter.drawText(0, 75, "POMPA")

    def mousePressEvent(self, event):
        self.dziala = not self.dziala
        self.update()
        super().mousePressEvent(event)

class OknoWykresu(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wykres Temperatury Pompy")
        self.resize(500, 350)
        layout = QVBoxLayout(self)
        
        self.graph = pg.PlotWidget()
        self.graph.setBackground('w')
        self.graph.showGrid(x=False, y=False)
        self.graph.setTitle("Temperatura Pompy", color="k", size="12pt")
        
        left_axis = self.graph.getAxis('left')
        left_axis.setPen('k')
        left_axis.setTextPen('k')
        bottom_axis = self.graph.getAxis('bottom')
        bottom_axis.setPen('k')
        bottom_axis.setTextPen('k')
        bottom_axis.setLabel('Czas (s)')

        layout.addWidget(self.graph)

        self.time_data = []
        self.temp_data = []
        self.line_temp = self.graph.plot(pen=pg.mkPen('r', width=3), name="Temp Pompy")

    def aktualizuj(self, czas, temp):
        self.time_data.append(czas)
        self.temp_data.append(temp)
        if len(self.time_data) > 100:
            self.time_data.pop(0)
            self.temp_data.pop(0)
        self.line_temp.setData(self.time_data, self.temp_data)
    
    def wyczysc(self):
        self.time_data = []
        self.temp_data = []
        self.line_temp.setData([], [])

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Symulacja")
        self.setGeometry(100, 100, 900, 600)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 800, 550)
        self.view = QGraphicsView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.setCentralWidget(self.view)

        self.z1 = Zbiornik(600, 50, nazwa="ZBIORNIK 1")
        self.scene.addItem(self.z1)
        self.z2 = Zbiornik(100, 50, nazwa="ZBIORNIK 2")
        self.scene.addItem(self.z2)
        self.z4 = Zbiornik(150, 380, nazwa="ZBIORNIK 4")
        self.scene.addItem(self.z4)
        self.z3 = Zbiornik(600, 380, nazwa="ZBIORNIK 3")
        self.scene.addItem(self.z3)

        self.pompa = Pompa(350, 220) 
        self.scene.addItem(self.pompa)

        self.rura1 = Rura([(640, 160), (140, 160)]) 
        self.scene.addItem(self.rura1)
        self.rura2 = Rura([(140, 160), (140, 260), (350, 260)]) 
        self.scene.addItem(self.rura2)
        self.rura3_out = Rura([(410, 260), (450, 260)])
        self.scene.addItem(self.rura3_out)
        self.rura_split = Rura([(450, 260), (450, 330)])
        self.scene.addItem(self.rura_split)
        self.rura_to_z4 = Rura([(450, 330), (190, 330), (190, 380)])
        self.scene.addItem(self.rura_to_z4)
        self.rura_to_z3 = Rura([(450, 330), (640, 330), (640, 380)])
        self.scene.addItem(self.rura_to_z3)

        lbl_z1 = QLabel("Poziom Z1 (%):", self)
        lbl_z1.setGeometry(600, 10, 100, 20)
        
        self.input_z1 = QLineEdit(self)
        self.input_z1.setGeometry(700, 10, 50, 25)
        self.input_z1.setPlaceholderText("0-100")
        self.input_z1.returnPressed.connect(self.ustaw_poziom_z1)

        start_x = 350
        start_y = 60
        total_width = 170
        lbl_cel = QLabel("Pożądana temperatura", self)
        lbl_cel.setGeometry(start_x, start_y, total_width, 20)
        lbl_cel.setAlignment(Qt.AlignCenter)
        
        self.target_temp = 20.0
        self.lbl_temp = QLabel(f"{self.target_temp:.1f} °C", self)
        self.lbl_temp.setGeometry(start_x + 40, start_y + 30, 90, 30) 
        self.lbl_temp.setAlignment(Qt.AlignCenter) 
        self.lbl_temp.setStyleSheet("font-weight: bold; font-size: 14px; border: 1px solid #ccc; background: white;")

        self.btn_minus = QPushButton("-", self)
        self.btn_minus.setGeometry(start_x, start_y + 30, 40, 30)
        self.btn_minus.setStyleSheet("background-color: #ff9999; font-weight: bold;")
        self.btn_minus.clicked.connect(lambda: self.zmien_temp(-0.5))

        self.btn_plus = QPushButton("+", self)
        self.btn_plus.setGeometry(start_x + 100, start_y + 30, 40, 30)
        self.btn_plus.setStyleSheet("background-color: #99ff99; font-weight: bold;")
        self.btn_plus.clicked.connect(lambda: self.zmien_temp(0.5))

        self.btn_wykres = QPushButton("Pokaż Wykres", self)
        self.btn_wykres.setGeometry(start_x, start_y + 80, 140, 30)
        self.btn_wykres.clicked.connect(self.pokaz_wykres)

        self.btn_reset = QPushButton("Wyczyść", self)
        self.btn_reset.setGeometry(start_x, start_y + 120, 140, 30)
        self.btn_reset.clicked.connect(self.reset_symulacji)

        self.timer = QTimer()
        self.timer.timeout.connect(self.symulacja)
        self.timer.start(100)
        
        self.czas_symulacji = 0.0
        self.okno_wykresu = None

    def ustaw_poziom_z1(self):
        tekst = self.input_z1.text()
        if tekst.isdigit():
            val = float(tekst)
            if val > 100:
                val = 100
            
            nowa_ilosc = self.z1.pojemnosc * (val / 100.0)
            self.z1.aktualna_ilosc = nowa_ilosc
            self.z1.update()

    def zmien_temp(self, delta):
        self.target_temp += delta
        self.lbl_temp.setText(f"{self.target_temp:.1f} °C")

    def pokaz_wykres(self):
        if self.okno_wykresu is None:
            self.okno_wykresu = OknoWykresu(self)
        self.okno_wykresu.show()

    def reset_symulacji(self):
        self.z1.aktualna_ilosc = 0
        self.z2.aktualna_ilosc = 0
        self.z3.aktualna_ilosc = 0
        self.z4.aktualna_ilosc = 0
        self.z3.temp_aktualna = 20.0
        self.z4.temp_aktualna = 20.0
        self.pompa.temp_aktualna = 20.0 
        self.target_temp = 20.0
        self.pompa.dziala = False
        self.czas_symulacji = 0.0
        self.input_z1.clear()
        
        for item in self.scene.items():
            if isinstance(item, Rura):
                item.ustaw_przeplyw(False)
        
        if self.okno_wykresu:
            self.okno_wykresu.wyczysc()
        self.scene.update()

    def symulacja(self):
        self.czas_symulacji += 0.1
        rate = 1.0 

        if self.z1.aktualna_ilosc > 0:
            amount = min(self.z1.aktualna_ilosc, rate)
            if self.z2.aktualna_ilosc < self.z2.pojemnosc:
                self.z1.aktualna_ilosc -= amount
                self.z2.aktualna_ilosc += amount
                self.rura1.ustaw_przeplyw(True)
            else:
                self.rura1.ustaw_przeplyw(False)
        else:
            self.rura1.ustaw_przeplyw(False)

        if self.z2.aktualna_ilosc > 0 and self.pompa.dziala:
            self.rura2.ustaw_przeplyw(True)
            self.rura3_out.ustaw_przeplyw(True)
            self.rura_split.ustaw_przeplyw(True)
            self.rura_to_z3.ustaw_przeplyw(True)
            self.rura_to_z4.ustaw_przeplyw(True)
            
            amount = min(self.z2.aktualna_ilosc, rate * 1.5)
            self.z2.aktualna_ilosc -= amount
            half = amount / 2
            
            if self.z3.aktualna_ilosc < self.z3.pojemnosc: self.z3.aktualna_ilosc += half
            if self.z4.aktualna_ilosc < self.z4.pojemnosc: self.z4.aktualna_ilosc += half
        else:
            self.rura2.ustaw_przeplyw(False)
            self.rura3_out.ustaw_przeplyw(False)
            self.rura_split.ustaw_przeplyw(False)
            self.rura_to_z3.ustaw_przeplyw(False)
            self.rura_to_z4.ustaw_przeplyw(False)

        wspolczynnik = 0.05
        
        if self.pompa.dziala:
            roznica = self.target_temp - self.pompa.temp_aktualna
            self.pompa.temp_aktualna += roznica * wspolczynnik
            if self.okno_wykresu and self.okno_wykresu.isVisible():
                self.okno_wykresu.aktualizuj(self.czas_symulacji, self.pompa.temp_aktualna)
        else:
            self.pompa.temp_aktualna += (20.0 - self.pompa.temp_aktualna) * wspolczynnik

        if self.z3.aktualna_ilosc > 0:
            self.z3.temp_aktualna += (self.pompa.temp_aktualna - self.z3.temp_aktualna) * wspolczynnik
            self.z4.temp_aktualna = self.z3.temp_aktualna
        
        self.scene.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())