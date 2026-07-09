#import datetime module
from datetime import date
import holidays

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

  def lid_1(self):
    """
    Maakt een lijst van algemeen erkende feestdagen genoemd in lid_1

    Deze functie achterhaalt de datum van de genoemde feestdagen in lid 1 en voegt deze samen in een lijst.

    Geeft terug:
      list[date]
    """
    lijst_feestdagen = []
    holidays_nl = holidays.NL(years= self.jaar, language='nl')
    for dag, naam_dag in holidays_nl.items():
      if (
        naam_dag == "Nieuwjaarsdag" or 
        naam_dag == "Tweede paasdag" or 
        naam_dag == "Tweede Pinksterdag" or 
        naam_dag == "Eerste Kerstdag" or
        naam_dag == "Tweede Kerstdag" or
        naam_dag == "Hemelvaartsdag" or
        naam_dag == "Koningsdag" or
        dag  == date(self.jaar,5,5)
        ):
        lijst_feestdagen.append(dag)
    
    return lijst_feestdagen

  def lid_2(self):
    """
    Achterhaalt de dag van Goede Vrijdag genoemd in lid_1.

    Deze functie achterhaalt de datum van de genoemde feestdagen in lid 2.

    Geeft terug:
      list[date]
    """
    holidays_nl = holidays.NL(years= self.jaar, language='nl')
    for dag, naam_dag in holidays_nl.items():
      if (naam_dag == "Goede Vrijdag"):
        return [dag]
      
  def lid_3(self):
    """
    Achterhaalt de dagen gelijkgesteld met de algemeen erkende feestdagen.

    Deze functie controleert welke dagen met algemeen erkende feestdagen zijn gelijkgesteld en geeft deze terug als deze dag is gelegen in het betreffende jaar.

    Geeft terug:
      list[date]
    """
    lijst_gelijkstelling_feestdagen = [
      date(2023,4,28), date(2023,5,19), date(2024,5,10), date(2024,12,27), date(2025,5,30), # Besluit gelijkstelling van 28 april 2023, 19 mei 2023, 10 mei 2024, 27 december 2024 en 30 mei 2025 met een algemeen erkende feestdag
      date(2026,2,2), date(2026,5,15), date(2027,5,7), date(2028,4,28), date(2025,5,26), # Besluit gelijkstelling van 2 januari 2026, 15 mei 2026, 7 mei 2027, 28 april 2028 en 26 mei 2028 met een algemeen erkende feestdag
      ]
    
    bereik_gelijkstelling_feestdagen = []
    for dag in lijst_gelijkstelling_feestdagen:
      if (dag.year == self.jaar):
        bereik_gelijkstelling_feestdagen.append(dag)

    return bereik_gelijkstelling_feestdagen