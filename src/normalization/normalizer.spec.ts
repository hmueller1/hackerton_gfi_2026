import { normalize } from './normalizer';

const validInput = {
  beruf: {
    beschreibung: 'Fachinformatiker Anwendungsentwicklung',
    berufNr: [4980],
    pruefungsBereiche: [
      {
        name: 'Projektarbeit',
        aufgaben: [
          {
            name: 'Aufgabe 1',
            struktur: 'Freitext',
            termin: {
              datum: '2026-05-10',
              uhrzeitvon: '09:00',
              uhrzeitbis: '12:00',
              dauer: 180,
            },
          },
        ],
      },
    ],
  },
};

describe('normalize', () => {
  it('gibt ein BerufDocument zurück bei validem Input', () => {
    const result = normalize(validInput);
    expect(result).not.toBeNull();
    expect(result?.beruf.beschreibung).toBe('Fachinformatiker Anwendungsentwicklung');
  });

  it('gibt null zurück bei fehlerhaftem Objekt', () => {
    const result = normalize({ beruf: { beschreibung: 123 } });
    expect(result).toBeNull();
  });

  it('gibt null zurück bei null als Input', () => {
    const result = normalize(null);
    expect(result).toBeNull();
  });
});
