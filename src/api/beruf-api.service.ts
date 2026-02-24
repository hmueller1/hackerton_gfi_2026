import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { Beruf, PruefungsBereich } from '../domain/interfaces';
import { BerufeDocument } from '../persistence/beruf.schema';
import { BerufRepository } from '../persistence/beruf.repository';

export type BerufApiResponse = {
  readonly _id: string;
  readonly filename: string;
  readonly beruf: Beruf;
};

const VON_DATUM_REGEX = /^\d{4}-\d{2}-\d{2}$/;

const validateVonDatum = (vonDatum: string): void => {
  if (!VON_DATUM_REGEX.test(vonDatum)) {
    throw new BadRequestException(`Ungültiges Datumsformat: "${vonDatum}". Erwartet: YYYY-MM-DD`);
  }
};

const filterBereiche = (
  bereiche: readonly PruefungsBereich[],
  vonDatum: string,
): readonly PruefungsBereich[] =>
  bereiche
    .map((bereich) => ({
      ...bereich,
      aufgaben: bereich.aufgaben.filter((aufgabe) => (aufgabe.termin.datum ?? '') >= vonDatum),
    }))
    .filter((bereich) => bereich.aufgaben.length > 0);

const toResponse = (doc: BerufeDocument): BerufApiResponse => ({
  _id: (doc._id as { toString(): string }).toString(),
  filename: doc.filename,
  beruf: doc.beruf,
});

const applyDateFilter = (
  responses: readonly BerufApiResponse[],
  vonDatum: string,
): readonly BerufApiResponse[] =>
  responses
    .map((r) => ({
      ...r,
      beruf: {
        ...r.beruf,
        pruefungsBereiche: filterBereiche(r.beruf.pruefungsBereiche, vonDatum),
      },
    }))
    .filter((r) => r.beruf.pruefungsBereiche.length > 0);

@Injectable()
export class BerufApiService {
  constructor(private readonly repository: BerufRepository) {}

  async findAll(vonDatum?: string): Promise<readonly BerufApiResponse[]> {
    if (vonDatum !== undefined) {
      validateVonDatum(vonDatum);
    }
    const docs = await this.repository.findAll();
    const responses = docs.map(toResponse);
    return vonDatum !== undefined ? applyDateFilter(responses, vonDatum) : responses;
  }

  async findById(id: string, vonDatum?: string): Promise<BerufApiResponse> {
    if (vonDatum !== undefined) {
      validateVonDatum(vonDatum);
    }
    const numericId = Number(id);
    const doc = Number.isInteger(numericId) && !Number.isNaN(numericId) && String(numericId) === id
      ? await this.repository.findByBerufNr(numericId)
      : await this.repository.findById(id);
    if (doc === null) {
      throw new NotFoundException(`Beruf mit ID "${id}" nicht gefunden`);
    }
    const response = toResponse(doc);
    if (vonDatum !== undefined) {
      const filtered = applyDateFilter([response], vonDatum);
      if (filtered.length === 0) {
        return { ...response, beruf: { ...response.beruf, pruefungsBereiche: [] } };
      }
      return filtered[0];
    }
    return response;
  }
}
