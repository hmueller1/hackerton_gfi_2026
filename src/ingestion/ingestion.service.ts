import { Injectable, Logger, OnApplicationBootstrap } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { readdir } from 'fs/promises';
import { join, basename } from 'path';
import { PdfReaderService } from './pdf-reader.service';
import { AiParserService } from './ai-parser.service';
import { BerufRepository } from '../persistence/beruf.repository';
import { normalize } from '../normalization/normalizer';

@Injectable()
export class IngestionService implements OnApplicationBootstrap {
  private readonly logger = new Logger(IngestionService.name);

  constructor(
    private readonly config: ConfigService,
    private readonly pdfReader: PdfReaderService,
    private readonly aiParser: AiParserService,
    private readonly berufRepository: BerufRepository,
  ) {}

  async onApplicationBootstrap(): Promise<void> {
    const pdfDir = this.config.get<string>('PDF_DIR', './doc/berufe/pages');
    const files = await readdir(pdfDir);
    const pdfFiles = files.filter((f) => f.endsWith('.pdf'));

    for (const file of pdfFiles) {
      const filename = basename(file);
      try {
        const exists = await this.berufRepository.existsByFilename(filename);
        if (exists) continue;

        const fullPath = join(pdfDir, file);
        const rawText = await this.pdfReader.extractText(fullPath);
        const rawJson = await this.aiParser.parse(rawText);
        const normalized = normalize(rawJson);

        if (normalized === null) {
          this.logger.warn(`Skipping ${filename}: normalization failed`);
          continue;
        }

        await this.berufRepository.save(filename, normalized);
        this.logger.log(`Saved ${filename}`);
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        this.logger.warn(`Error processing ${filename}: ${message}`);
      }
    }
  }
}
