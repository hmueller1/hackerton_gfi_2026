import { Controller, Get, Param, Query } from '@nestjs/common';
import { BerufApiResponse, BerufApiService } from './beruf-api.service';

@Controller('berufe')
export class BerufApiController {
  constructor(private readonly service: BerufApiService) {}

  @Get()
  findAll(@Query('vonDatum') vonDatum?: string): Promise<readonly BerufApiResponse[]> {
    return this.service.findAll(vonDatum);
  }

  @Get(':id')
  findById(
    @Param('id') id: string,
    @Query('vonDatum') vonDatum?: string,
  ): Promise<BerufApiResponse> {
    return this.service.findById(id, vonDatum);
  }
}
