import { Module } from '@nestjs/common';
import { PersistenceModule } from '../persistence/persistence.module';
import { BerufApiService } from './beruf-api.service';
import { BerufApiController } from './beruf-api.controller';

@Module({
  imports: [PersistenceModule],
  providers: [BerufApiService],
  controllers: [BerufApiController],
})
export class ApiModule {}
