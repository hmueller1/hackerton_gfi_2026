import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { MongooseModule } from '@nestjs/mongoose';
import { BERUFE_COLLECTION, BerufSchemaDefinition } from './beruf.schema';
import { BerufRepository } from './beruf.repository';
import {
  FAILED_INGESTIONS_COLLECTION,
  FailedIngestionSchemaDefinition,
} from './failed-ingestion.schema';
import { FailedIngestionRepository } from './failed-ingestion.repository';

@Module({
  imports: [
    ConfigModule,
    MongooseModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        uri: config.getOrThrow<string>('MONGODB_URI'),
      }),
      inject: [ConfigService],
    }),
    MongooseModule.forFeature([
      { name: BERUFE_COLLECTION, schema: BerufSchemaDefinition },
      { name: FAILED_INGESTIONS_COLLECTION, schema: FailedIngestionSchemaDefinition },
    ]),
  ],
  providers: [BerufRepository, FailedIngestionRepository],
  exports: [BerufRepository, FailedIngestionRepository],
})
export class PersistenceModule {}
