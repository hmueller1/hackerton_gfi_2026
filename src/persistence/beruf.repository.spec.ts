import { getModelToken } from '@nestjs/mongoose';
import { Test, TestingModule } from '@nestjs/testing';
import { BERUFE_COLLECTION } from './beruf.schema';
import { BerufRepository } from './beruf.repository';

const mockModel = {
  countDocuments: jest.fn(),
  create: jest.fn(),
  find: jest.fn(),
  findById: jest.fn(),
};

describe('BerufRepository', () => {
  let repository: BerufRepository;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        BerufRepository,
        { provide: getModelToken(BERUFE_COLLECTION), useValue: mockModel },
      ],
    }).compile();
    repository = module.get<BerufRepository>(BerufRepository);
    jest.clearAllMocks();
  });

  describe('existsByFilename', () => {
    it('gibt true zurück wenn ein Dokument mit dem Dateinamen existiert (AC3)', async () => {
      mockModel.countDocuments.mockReturnValue({ exec: jest.fn().mockResolvedValue(1) });
      const result = await repository.existsByFilename('test.pdf');
      expect(result).toBe(true);
      expect(mockModel.countDocuments).toHaveBeenCalledWith({ filename: 'test.pdf' });
    });

    it('gibt false zurück wenn kein Dokument mit dem Dateinamen existiert (AC3)', async () => {
      mockModel.countDocuments.mockReturnValue({ exec: jest.fn().mockResolvedValue(0) });
      const result = await repository.existsByFilename('unbekannt.pdf');
      expect(result).toBe(false);
    });
  });
});
