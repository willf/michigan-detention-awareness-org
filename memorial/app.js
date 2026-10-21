(() => {
  'use strict';
  const data = window.MEMORIAL_DATA;
  const timeline = window.MemorialTimeline.createTimeline(data.records, data.cutoff);
  const wall = document.getElementById('names');
  const preview = document.getElementById('hover-card');
  const dialog = document.getElementById('record-dialog');
  const hover = window.matchMedia('(hover: hover) and (min-width: 701px)');
  const states = {AL:'Alabama',AZ:'Arizona',CA:'California',CO:'Colorado',FL:'Florida',GA:'Georgia',IL:'Illinois',IN:'Indiana',LA:'Louisiana',MA:'Massachusetts',MD:'Maryland',MI:'Michigan',MN:'Minnesota',MO:'Missouri',MP:'Northern Mariana Islands',MS:'Mississippi',NC:'North Carolina',NE:'Nebraska',NJ:'New Jersey',NM:'New Mexico',NV:'Nevada',NY:'New York',OH:'Ohio',PA:'Pennsylvania',PR:'Puerto Rico',RI:'Rhode Island',SC:'South Carolina',TX:'Texas',UT:'Utah',VA:'Virginia',WA:'Washington'};
  const formatDate = value => new Intl.DateTimeFormat('en-US', {year:'numeric',month:'long',day:'numeric',timeZone:'UTC'}).format(new Date(value + 'T12:00:00Z'));
  const safe = value => value === null || value === undefined || value === '' ? 'Not recorded' : String(value);
  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  function recordContent(record, isPreview) {
    const fragment = document.createDocumentFragment();
    const title = element('h2','record-title',record.name);
    if (!isPreview) title.id = 'record-name';
    fragment.append(title);
    const details = element('dl','record-details');
    const fields = [
      ['Nationality',record.nationality,''],
      ['Age',record.age === null ? null : `${record.age} years`,''],
      ['Date of death',formatDate(record.dateOfDeath),'wide date-row'],
      ['Last detention facility',record.lastDetentionFacility,'wide'],
      ['Actual death location — city',record.deathLocationCity,''],
      ['Actual death location — state',states[record.deathLocationState] || record.deathLocationState,''],
    ];
    for (const [label, value, className] of fields) {
      const group = element('div',className);
      group.append(element('dt','',label),element('dd','',safe(value)));
      details.append(group);
    }
    fragment.append(details);
    if (isPreview) fragment.append(element('p','preview-help','Select the name to keep this record open.'));
    return fragment;
  }
  let hideTimer;
  let suppressFocusPreview = false;
  const hidePreview = () => {clearTimeout(hideTimer);preview.hidden = true;};
  const scheduleHide = () => {clearTimeout(hideTimer);hideTimer = setTimeout(hidePreview,180);};
  function showPreview(record, button) {
    if (!hover.matches || dialog.open || suppressFocusPreview) return;
    clearTimeout(hideTimer);
    preview.replaceChildren(recordContent(record,true));
    preview.hidden = false;
    const bounds = button.getBoundingClientRect();
    // Place the record on the opposite side of the name; keep it within the viewport.
    const left = bounds.left + bounds.width / 2 < innerWidth / 2 ? innerWidth - preview.offsetWidth - 24 : 24;
    preview.style.left = Math.max(16,left) + 'px';
    preview.style.top = Math.max(16,Math.min(bounds.top,innerHeight-preview.offsetHeight-16)) + 'px';
  }
  let lastRenderedYear = null;
  function appendRecords(records) {
    let firstButton = null;
    for (const record of records) {
      const year = record.dateOfDeath.slice(0,4);
      if (year !== lastRenderedYear) {
        const divider = element('li',lastRenderedYear === null ? 'year-divider year-start' : 'year-divider');
        divider.setAttribute('role','presentation');
        divider.append(element('h2','year-label',year));
        wall.append(divider);
      }
      lastRenderedYear = year;
      const item = element('li');
      item.dataset.year = year;
      const button = element('button','name-button',record.name);
      button.type = 'button';
      button.setAttribute('aria-haspopup','dialog');
      button.setAttribute('aria-controls','record-dialog');
      button.dataset.recordId = record.id;
      button.addEventListener('pointerenter',event => {if(event.pointerType !== 'touch') showPreview(record,button);});
      button.addEventListener('pointerleave',scheduleHide);
      button.addEventListener('focus',() => showPreview(record,button));
      button.addEventListener('blur',scheduleHide);
      button.addEventListener('click',() => {
        hidePreview();
        document.getElementById('record-content').replaceChildren(recordContent(record,false));
        dialog.showModal();
      });
      item.append(button);
      wall.append(item);
      firstButton ||= button;
    }
    return firstButton;
  }
  preview.addEventListener('pointerenter',() => clearTimeout(hideTimer));
  preview.addEventListener('pointerleave',scheduleHide);
  document.addEventListener('keydown',event => {if(event.key === 'Escape') {hidePreview();suppressFocusPreview = true;setTimeout(() => {suppressFocusPreview=false;},100);}});
  window.addEventListener('scroll',hidePreview,{passive:true});
  window.addEventListener('resize',hidePreview);
  hover.addEventListener('change',hidePreview);
  dialog.addEventListener('close',() => {hidePreview();suppressFocusPreview=true;setTimeout(() => {suppressFocusPreview=false;},100);});
  dialog.addEventListener('click',event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if(event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  const controls = document.getElementById('earlier-controls');
  const loadButton = document.getElementById('load-earlier');
  const range = document.getElementById('earlier-range');
  const status = document.getElementById('load-status');
  const earliestDate = data.records.reduce((earliest, record) => !earliest || record.dateOfDeath < earliest ? record.dateOfDeath : earliest, null);
  document.getElementById('record-count').textContent = `${data.records.length} Deaths in ICE Detention`;
  document.getElementById('footer-since').textContent = earliestDate ? `Since ${formatDate(earliestDate)}` : '';
  function periodLabel(period) {
    const last = new Date(period.end + 'T12:00:00Z');
    last.setUTCDate(last.getUTCDate() - 1);
    return `${formatDate(period.start)} – ${formatDate(last.toISOString().slice(0,10))}`;
  }
  function loadEarlier(initial = false) {
    const batch = timeline.takeNext();
    if (!batch) return;
    hidePreview();
    const firstNew = appendRecords(batch.records);
    document.getElementById('subtitle-since').textContent = `since ${formatDate(batch.cutoff)}`;
    const next = timeline.nextPeriod();
    controls.hidden = !next;
    range.textContent = next ? periodLabel(next) : '';
    if (!initial) {
      status.textContent = `${batch.records.length} earlier ${batch.records.length === 1 ? 'name' : 'names'} added for ${periodLabel(batch.period)}. ${batch.shown} names now shown, since ${formatDate(batch.cutoff)}.${next ? '' : ' All available names are now shown.'}`;
      if (firstNew) {
        suppressFocusPreview = true;
        firstNew.focus({preventScroll:true});
        firstNew.scrollIntoView({block:'nearest'});
        setTimeout(() => {suppressFocusPreview=false;},100);
      }
    }
  }
  loadButton.addEventListener('click',() => loadEarlier());
  loadEarlier(true);
})();
