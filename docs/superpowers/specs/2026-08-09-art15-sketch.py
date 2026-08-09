from dataclasses import dataclass
from taxlation.nl.feiten import Casus

WAARDEGRENS = 525_000
LEEFTIJD_MINIMUM = 18
LEEFTIJD_MAXIMUM = 35  # exclusief


@dataclass
class Artikel15:
    """Artikel 15 WBRV."""
    casus: Casus

    @dataclass
    class Lid1:
        """Artikel 15, lid 1 WBRV."""
        casus: Casus

        @dataclass
        class OnderdeelP:
            """Artikel 15, lid 1, onderdeel p WBRV — startersvrijstelling."""
            casus: Casus
            VEREIST = (
                ("zaak.woning", "zaak.rechten_woning_onderworpen",
                 "zaak.rechten_lidmaatschap_woning"),
                "verkrijger.natuurlijk_persoon",
                "verkrijger.leeftijd",
                "verkrijger.vrijstelling_eerder_toegepast",
                "verkrijger.verklaring_vrijstelling",
                "hoofdverblijf.woning_tijdelijk_hoofdverblijf",
                "hoofdverblijf.verklaring_hoofdverblijf",
                "zaak.waarde_woning",
            )

            @property
            def startersvrijstelling(self) -> bool:
                self.casus.vereist(self.VEREIST, "Artikel15.Lid1.OnderdeelP")
                return (self._verkrijging_woning and self._verkrijger_kwalificeert
                        and self._eenmalig_beroep and self._hoofdverblijfeis
                        and self._binnen_waardegrens)

            @property
            def _verkrijging_woning(self) -> bool:
                z = self.casus.zaak
                return bool(z.woning or z.rechten_woning_onderworpen
                            or z.rechten_lidmaatschap_woning)

            @property
            def _verkrijger_kwalificeert(self) -> bool:
                v = self.casus.verkrijger
                return v.natuurlijk_persoon and LEEFTIJD_MINIMUM <= v.leeftijd < LEEFTIJD_MAXIMUM

            @property
            def _eenmalig_beroep(self) -> bool:
                v = self.casus.verkrijger
                return not v.vrijstelling_eerder_toegepast and v.verklaring_vrijstelling

            @property
            def _hoofdverblijfeis(self) -> bool:
                h = self.casus.hoofdverblijf
                return not h.woning_tijdelijk_hoofdverblijf and h.verklaring_hoofdverblijf

            @property
            def _binnen_waardegrens(self) -> bool:
                z = self.casus.zaak
                return (z.waarde_woning + z.waarde_aanhorigheden) <= WAARDEGRENS

        @property
        def onderdeel_p(self) -> bool:
            return Artikel15.Lid1.OnderdeelP(self.casus).startersvrijstelling

    @property
    def lid_1(self) -> bool:
        return Artikel15.Lid1(self.casus).onderdeel_p
