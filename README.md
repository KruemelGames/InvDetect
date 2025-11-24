# InvDetect
Small concept for implementation into bigger project. Allows user to scan inventory for all items.


Python Projekt in C:\Users\%USERPROFILE%\PycharmProjects\InvDetect
Mit python 3.11.3
Ziel des Projekts, Erkennung von Items per Mouse-Over im Spiel Star Citizen aus dem Inventar mithilfe von Screenshots und OCR (Tesseract (bereits installiert auf C:\Program Files\Tesseract-OCR))
Durchführung des Ablaufs:
Einfügen wird auf der Tastatur im Spiel gedrückt. Das wird im Hintergrund vom Programm erkannt
Mauszeiger steht bereits auf einer Kachel. Screenshot, von Bereich 100px senkrecht 1095px horizontal bis 135px senkrecht 1326px horizontal. Danach bewegt sich der Mauszeiger zur nächsten Kachel. Wieder Screenshot von festgelegtem Bereich.
Die Kacheln sind in Reihenfolge 4*X
Das heißt es liegen 4 Kacheln maximal nebeneinander. und X nach unten.
Es gibt 2 Arten von Kacheln die erkannt werden müssen.

```
1x1 86px(horizontal Breite)*86(senkrecht höhe)px
1x2 86px(horizontal Breite)*160(senkrecht höhe)px
```

Der Abstand zwischen den Kacheln beträgt immer 10px (horizontal und senkrecht)
Schwierigkeit: Es muss ab und zu immer nach unten gescrollt werden um die Liste nach oben zu schieben um die Items unten mit aufzunehmen.

Der gesamte Inventarbereich ist ab 220px bis 1021px senkrecht und 1348px bis 1790px waagerecht
Der gesamte Bildschirmbereich selbst ist 1920x1080.
Ab Inventar Rahmen Oben bis zur ersten Kachel drunter ist ein Abstand von 4px.
Ab Inventar Rahmen Links bis zur ersten kachel rechts ist ein Abstand von 4px.

Die Screenshots sollen analysiert werden per OCR und der Text soll erkannt werden.
Sollte "Volume: * μSCU" erkannt werden soll dies rausgefiltert werden "*" steht hier für einen sich ändernden Wert.
Der erkannte Text soll dann in eine TXT eingetragen werden mit Umbruch.
Der Text ist leider nur 10px hoch.
