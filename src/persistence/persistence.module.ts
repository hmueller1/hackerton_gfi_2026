import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { MongooseModule } from '@nestjs/mongoose';
import { BERUFE_COLLECTION, BerufSchemaDefinition } from './beruf.schema';
import { BerufRepository } from './beruf.repository';

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
    ]),
  ],
  providers: [BerufRepository],
  exports: [BerufRepository],
})
export class PersistenceModule {}

