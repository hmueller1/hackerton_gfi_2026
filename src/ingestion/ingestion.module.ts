import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { PersistenceModule } from '../persistence/persistence.module';
import { PdfReaderService } from './pdf-reader.service';
import { AiParserService } from './ai-parser.service';
import { IngestionService } from './ingestion.service';

@Module({
  imports: [PersistenceModule, ConfigModule],
  providers: [PdfReaderService, AiParserService, IngestionService],
})
export class IngestionModule {}
