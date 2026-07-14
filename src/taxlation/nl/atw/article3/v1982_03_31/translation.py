#import datetime module
from datetime import date, timedelta

#import dataclasses module
from dataclasses import dataclass

@dataclass
class Artikel3:
  """
  Dataclass voor Art. 3 Algemene termijnenwet
  """
  jaar: int # jaar van feestdagen

  @property
  def algemeen_erkende_feestdagen(self) -> list[date]:
    """
    Maakt een gesorteerde lijst van algemeen erkende feestdagen.

    Functie voegt de feestdagen op basis van lid 1, 2 en 3 samen

    Geeft terug:
      list[date]
    """
    lijst_algemeen_erkende_feestdagen = (self.lid_1())
    lijst_algemeen_erkende_feestdagen.extend(self.lid_2())
    lijst_algemeen_erkende_feestdagen.extend(self.lid_3())

    return sorted(lijst_algemeen_erkende_feestdagen)

  def lid_1(self) -> list[date]:
    """
    Maakt een lijst van algemeen erkende feestdagen genoemd in lid_1

    Deze functie achterhaalt de datum van de genoemde feestdagen in lid 1 en voegt deze samen in een lijst.

    Geeft terug:
      list[date]
    """
    eerste_paasdag = self._bereken_eerste_paasdag()
    koningsdag = self._bereken_koningsdag()

    return [
      date(self.jaar, 1, 1), # Nieuwjaarsdag
      eerste_paasdag + timedelta(days=1), # Tweede Paasdag
      eerste_paasdag + timedelta(days=50), # Tweede Pinksterdag
      date(self.jaar, 12, 25), # Eerste Kerstdag
      date(self.jaar, 12, 26), # Tweede Kerstdag
      eerste_paasdag + timedelta(days=39), # Hemelvaartsdag
      koningsdag, # Koningsdag
      date(self.jaar, 5, 5) # vijfde mei
    ]

  def lid_2(self) -> list[date]:
    """
    Achterhaalt de dag van Goede Vrijdag genoemd in lid_1.

    Deze functie achterhaalt de datum van de genoemde feestdagen in lid 2.

    Geeft terug:
      list[date]
    """
    eerste_paasdag = self._bereken_eerste_paasdag()

    return [eerste_paasdag - timedelta(days=2)]
      
  def lid_3(self) -> list[date]:
    """
    Achterhaalt de dagen gelijkgesteld met de algemeen erkende feestdagen.

    Deze functie controleert welke dagen met algemeen erkende feestdagen zijn gelijkgesteld en geeft deze terug als deze dag is gelegen in het betreffende jaar.

    Geeft terug:
      list[date]
    """
    lijst_gelijkstelling_feestdagen = [
      date(2023,4,28), date(2023,5,19), date(2024,5,10), date(2024,12,27), date(2025,5,30), # Besluit gelijkstelling van 28 april 2023, 19 mei 2023, 10 mei 2024, 27 december 2024 en 30 mei 2025 met een algemeen erkende feestdag
      date(2026,1,2), date(2026,5,15), date(2027,5,7), date(2028,4,28), date(2028,5,26), # Besluit gelijkstelling van 2 januari 2026, 15 mei 2026, 7 mei 2027, 28 april 2028 en 26 mei 2028 met een algemeen erkende feestdag
      ]
    
    bereik_gelijkstelling_feestdagen = []
    for dag in lijst_gelijkstelling_feestdagen:
      if (dag.year == self.jaar):
        bereik_gelijkstelling_feestdagen.append(dag)

    return bereik_gelijkstelling_feestdagen
  
  def _bereken_eerste_paasdag(self) -> date:
    """
    Berekent de datum waarop eerste paasdag valt.

    Deze functie achterhaalt de datum van eerste paasdag volgens het algoritme van Gauss.

    Geeft terug:
      date
    """
    a = self.jaar % 19
    b = self.jaar // 100
    c = self.jaar % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451

    maand = (h + l - 7 * m + 114) // 31
    dag = 1 + ((h + l - 7 * m + 114) % 31)

    return date(self.jaar, maand, dag)
  
  def _bereken_koningsdag(self) -> date:
    """
    Berekent de datum waarop Koningsdag valt.

    Deze functie achterhaalt de datum van Koningsdag.

    Geeft terug:
      date
    """
    if self.jaar < 2014:
      koningsdag = date(self.jaar, 4, 30)
    elif  self.jaar >= 2014: 
      koningsdag = date(self.jaar, 4, 27)

    if koningsdag.weekday() == 6:
      koningsdag -= timedelta(days=1)
    
    return koningsdag