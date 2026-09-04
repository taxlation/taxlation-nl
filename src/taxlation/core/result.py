from dataclasses import dataclass
import json

@dataclass
class Result():
    origin: str
    result: bool
    explanation: str
    trail: tuple["Result", ...] = ()

    def __bool__(self) -> bool:  # zodat je 'm nog in if/and kunt gebruiken
      return self.result

    def to_dict(self) -> dict:
      d = {
        "origin": self.origin,
        "result": self.result,
        "explanation": self.explanation
      }

      if self.trail:
        d["trail"] = [s.to_dict() for s in self.trail]

      return d

    def __repr__(self) -> str:
       return json.dumps(self.to_dict(), ensure_ascii= False, indent=2)