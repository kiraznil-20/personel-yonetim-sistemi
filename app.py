from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "personel-sistemi-gizli-anahtar"

KLASOR_YOLU = os.path.dirname(os.path.abspath(__file__))
VERITABANI_YOLU = os.path.join(KLASOR_YOLU, "database.db")


def veritabani_baglantisi():
    conn = sqlite3.connect(VERITABANI_YOLU)
    conn.row_factory = sqlite3.Row
    return conn


def veritabani_olustur():
    conn = veritabani_baglantisi()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS Personel (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Ad TEXT NOT NULL,
            Soyad TEXT NOT NULL,
            Bolum TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


veritabani_olustur()


def giris_gerekli(f):
    @wraps(f)
    def kontrol(*args, **kwargs):
        if "kullanici" not in session:
            return redirect(url_for("giris"))

        return f(*args, **kwargs)

    return kontrol


@app.route("/giris", methods=["GET", "POST"])
def giris():
    hata = ""

    if request.method == "POST":
        kullanici_adi = request.form["kullanici_adi"]
        sifre = request.form["sifre"]

        if kullanici_adi == "admin" and sifre == "1234":
            session["kullanici"] = kullanici_adi
            return redirect(url_for("ana_sayfa"))

        hata = "Kullanıcı adı veya şifre yanlış."

    return render_template("login.html", hata=hata)


@app.route("/cikis")
def cikis():
    session.clear()
    return redirect(url_for("giris"))


@app.route("/")
@giris_gerekli
def ana_sayfa():
    arama = request.args.get("arama", "").strip()

    conn = veritabani_baglantisi()

    if arama:
        personeller = conn.execute(
            """
            SELECT * FROM Personel
            WHERE Ad LIKE ?
               OR Soyad LIKE ?
               OR Bolum LIKE ?
            """,
            (f"%{arama}%", f"%{arama}%", f"%{arama}%")
        ).fetchall()
    else:
        personeller = conn.execute(
            "SELECT * FROM Personel"
        ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        personeller=personeller,
        arama=arama
    )


@app.route("/personel-ekle", methods=["POST"])
@giris_gerekli
def personel_ekle():
    ad = request.form["ad"]
    soyad = request.form["soyad"]
    bolum = request.form["bolum"]

    conn = veritabani_baglantisi()

    conn.execute(
        "INSERT INTO Personel (Ad, Soyad, Bolum) VALUES (?, ?, ?)",
        (ad, soyad, bolum)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("ana_sayfa"))


@app.route("/personel-sil/<int:id>", methods=["POST"])
@giris_gerekli
def personel_sil(id):
    conn = veritabani_baglantisi()

    conn.execute(
        "DELETE FROM Personel WHERE ID = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("ana_sayfa"))


@app.route("/personel-duzenle/<int:id>", methods=["GET", "POST"])
@giris_gerekli
def personel_duzenle(id):
    conn = veritabani_baglantisi()

    if request.method == "POST":
        ad = request.form["ad"]
        soyad = request.form["soyad"]
        bolum = request.form["bolum"]

        conn.execute(
            """
            UPDATE Personel
            SET Ad = ?, Soyad = ?, Bolum = ?
            WHERE ID = ?
            """,
            (ad, soyad, bolum, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("ana_sayfa"))

    personel = conn.execute(
        "SELECT * FROM Personel WHERE ID = ?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template(
        "duzenle.html",
        personel=personel
    )


if __name__ == "__main__":
    app.run(debug=True)