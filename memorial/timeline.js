(() => {
  'use strict';
  const iso = date => date.toISOString().slice(0, 10);
  const parse = value => new Date(value + 'T00:00:00Z');
  function followingDay(value) {
    const date = parse(value);
    date.setUTCDate(date.getUTCDate() + 1);
    return iso(date);
  }
  function monthsBefore(value, months) {
    const date = parse(value);
    const target = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() - months, 1));
    const lastDay = new Date(Date.UTC(target.getUTCFullYear(), target.getUTCMonth() + 1, 0)).getUTCDate();
    target.setUTCDate(Math.min(date.getUTCDate(),lastDay));
    return iso(target);
  }

  function createTimeline(sourceRecords, cutoff) {
    const records = [...sourceRecords].sort((a, b) =>
      b.dateOfDeath.localeCompare(a.dateOfDeath) || a.name.localeCompare(b.name)
    );
    let initial = true;
    let step = 0;
    let cursor = 0;

    function nextPeriod() {
      if (initial) return {cutoff, start:cutoff, end:followingDay(records[0]?.dateOfDeath || cutoff)};
      if (cursor >= records.length) return null;
      const previousCutoff = monthsBefore(cutoff, step * 12);
      const nextCutoff = monthsBefore(cutoff, (step + 1) * 12);
      return {cutoff:nextCutoff, start:nextCutoff, end:previousCutoff};
    }

    function takeNext() {
      const period = nextPeriod();
      if (!period) return null;
      const batch = [];
      while (cursor < records.length && records[cursor].dateOfDeath >= period.start) {
        batch.push(records[cursor++]);
      }
      if (initial) initial = false;
      else step++;
      return {records: batch, period, shown: cursor, total: records.length, cutoff:period.cutoff};
    }

    return {takeNext, nextPeriod};
  }

  window.MemorialTimeline = {createTimeline};
})();
