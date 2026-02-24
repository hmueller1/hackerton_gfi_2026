import { ConfigService } from '@nestjs/config';
import { Test, TestingModule } from '@nestjs/testing';
import { AiParserService } from './ai-parser.service';
import { IngestionService } from './ingestion.service';
import { PdfReaderService } from './pdf-reader.service';
import { BerufRepository } from '../persistence/beruf.repository';

jest.mock('fs/promises', () => ({
  readdir: jest.fn().mockResolvedValue(['test.pdf', 'other.pdf']),
}));

jest.mock('../normalization/normalizer', () => ({
  normalize: jest.fn(),
}));

import { readdir } from 'fs/promises';
import { normalize } from '../normalization/normalizer';

const mockReaddir = readdir as jest.Mock;
const mockNormalize = normalize as jest.Mock;

const mockConfig = { get: jest.fn().mockReturnValue('./doc') };
const mockPdfReader = { extractText: jest.fn().mockResolvedValue('raw text') };
const mockAiParser = { parse: jest.fn().mockResolvedValue({ raw: 'json' }) };
const mockRepository = {
  existsByFilename: jest.fn(),
  save: jest.fn(),
};

describe('IngestionService', () => {
  let service: IngestionService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        IngestionService,
        { provide: ConfigService, useValue: mockConfig },
        { provide: PdfReaderService, useValue: mockPdfReader },
        { provide: AiParserService, useValue: mockAiParser },
        { provide: BerufRepository, useValue: mockRepository },
      ],
    }).compile();
    service = module.get<IngestionService>(IngestionService);
    jest.clearAllMocks();
  });

  it('überspringt bereits eingelesene Dateien ohne KI-Aufruf (AC2)', async () => {
    mockReaddir.mockResolvedValue(['test.pdf']);
    mockRepository.existsByFilename.mockResolvedValue(true);

    await service.onApplicationBootstrap();

    expect(mockAiParser.parse).not.toHaveBeenCalled();
    expect(mockRepository.save).not.toHaveBeenCalled();
  });

  it('speichert keine Datei wenn Normalisierung fehlschlägt (AC5)', async () => {
    mockReaddir.mockResolvedValue(['broken.pdf']);
    mockRepository.existsByFilename.mockResolvedValue(false);
    mockPdfReader.extractText.mockResolvedValue('text');
    mockAiParser.parse.mockResolvedValue({});
    mockNormalize.mockReturnValue(null);

    await service.onApplicationBootstrap();

    expect(mockRepository.save).not.toHaveBeenCalled();
  });

  it('speichert keine Datei wenn AI-Parser eine Exception wirft (AC5)', async () => {
    mockReaddir.mockResolvedValue(['error.pdf']);
    mockRepository.existsByFilename.mockResolvedValue(false);
    mockPdfReader.extractText.mockResolvedValue('text');
    mockAiParser.parse.mockRejectedValue(new Error('AI unreachable'));

    await service.onApplicationBootstrap();

    expect(mockRepository.save).not.toHaveBeenCalled();
  });

  it('verarbeitet neue Datei vollständig und speichert sie', async () => {
    const fakeDoc = { beruf: { beschreibung: 'Test', berufNr: [1], pruefungsBereiche: [] } };
    mockReaddir.mockResolvedValue(['new.pdf']);
    mockRepository.existsByFilename.mockResolvedValue(false);
    mockPdfReader.extractText.mockResolvedValue('text');
    mockAiParser.parse.mockResolvedValue({});
    mockNormalize.mockReturnValue(fakeDoc);

    await service.onApplicationBootstrap();

    expect(mockRepository.save).toHaveBeenCalledWith('new.pdf', fakeDoc);
  });
});
