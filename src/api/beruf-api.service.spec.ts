import { BadRequestException, NotFoundException } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { BerufApiService } from './beruf-api.service';
import { BerufRepository } from '../persistence/beruf.repository';
import { Beruf } from '../domain/interfaces';

const mockBeruf: Beruf = {
  beschreibung: 'Fachinformatiker',
  berufNr: [1234],
  pruefungsBereiche: [
    {
      name: 'Bereich A',
      aufgaben: [
        {
          name: 'Aufgabe 1',
          struktur: 'schriftlich',
          termin: { datum: '2026-03-15', uhrzeitvon: '09:00', uhrzeitbis: '12:00', dauer: 180 },
        },
        {
          name: 'Aufgabe 2',
          struktur: 'schriftlich',
          termin: { datum: '2025-11-01', uhrzeitvon: '09:00', uhrzeitbis: '11:00', dauer: 120 },
        },
      ],
    },
    {
      name: 'Bereich B',
      aufgaben: [
        {
          name: 'Aufgabe 3',
          struktur: 'mündlich',
          termin: { datum: '2025-10-01', uhrzeitvon: '13:00', uhrzeitbis: '14:00', dauer: 60 },
        },
      ],
    },
  ],
};

const mockDoc = {
  _id: { toString: () => 'abc123' },
  filename: 'test.pdf',
  beruf: mockBeruf,
};

const mockRepository = {
  findAll: jest.fn(),
  findById: jest.fn(),
};

describe('BerufApiService', () => {
  let service: BerufApiService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        BerufApiService,
        { provide: BerufRepository, useValue: mockRepository },
      ],
    }).compile();
    service = module.get<BerufApiService>(BerufApiService);
    jest.clearAllMocks();
  });

  describe('findAll', () => {
    it('gibt alle Berufe zurück wenn kein Datum angegeben', async () => {
      mockRepository.findAll.mockResolvedValue([mockDoc]);
      const result = await service.findAll();
      expect(result).toHaveLength(1);
      expect(result[0]._id).toBe('abc123');
      expect(result[0].filename).toBe('test.pdf');
    });

    it('filtert korrekt nach vonDatum (AC-2)', async () => {
      mockRepository.findAll.mockResolvedValue([mockDoc]);
      const result = await service.findAll('2026-01-01');
      expect(result).toHaveLength(1);
      const bereiche = result[0].beruf.pruefungsBereiche;
      expect(bereiche).toHaveLength(1);
      expect(bereiche[0].name).toBe('Bereich A');
      expect(bereiche[0].aufgaben).toHaveLength(1);
      expect(bereiche[0].aufgaben[0].termin.datum).toBe('2026-03-15');
    });

    it('gibt leeres Array zurück wenn alle Berufe herausgefiltert werden', async () => {
      mockRepository.findAll.mockResolvedValue([mockDoc]);
      const result = await service.findAll('2027-01-01');
      expect(result).toHaveLength(0);
    });

    it('wirft BadRequestException bei ungültigem vonDatum (AC-3)', async () => {
      await expect(service.findAll('kein-datum')).rejects.toThrow(BadRequestException);
    });
  });

  describe('findById', () => {
    it('gibt Beruf zurück bei gültiger ID (AC-4)', async () => {
      mockRepository.findById.mockResolvedValue(mockDoc);
      const result = await service.findById('abc123');
      expect(result._id).toBe('abc123');
    });

    it('wirft NotFoundException bei unbekannter ID (AC-5)', async () => {
      mockRepository.findById.mockResolvedValue(null);
      await expect(service.findById('unbekannt')).rejects.toThrow(NotFoundException);
    });

    it('wirft BadRequestException bei ungültigem vonDatum (AC-3)', async () => {
      mockRepository.findById.mockResolvedValue(mockDoc);
      await expect(service.findById('abc123', 'falsch')).rejects.toThrow(BadRequestException);
    });
  });
});
