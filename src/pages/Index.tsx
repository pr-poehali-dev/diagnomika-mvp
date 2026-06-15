import { useState, useEffect, useRef } from 'react';
import Icon from '@/components/ui/icon';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

const CHARACTER_IMG =
  'https://cdn.poehali.dev/projects/cb7818a8-cd7f-40ae-8055-7881cf09d17e/files/763ee90f-b510-426b-9358-16a0289dc20e.jpg';

const HAPPY_IMG =
  'https://cdn.poehali.dev/projects/cb7818a8-cd7f-40ae-8055-7881cf09d17e/bucket/d73b18e4-c011-4ee3-9799-f70f51e71808.png';

const STORY_LINES = [
  'Привет 👋',
  'Меня зовут Happy.',
  'Когда-то Артём начал искать ответ на простой вопрос:',
  '«Почему одни люди живут своей жизнью, а другие постоянно пытаются стать кем-то ещё?»',
  'Много лет он наблюдал за людьми, изучал тело, разум и душу, искал закономерности — и однажды заметил меня.',
  'Я — его внутренний персонаж.',
  'Я та часть, которая любит жить, исследовать мир, радоваться мелочам и напоминать, что жизнь — это не только цели и достижения.',
  'Так появилась Диагномика.',
  'Теперь пришло время познакомиться с твоим внутренним персонажем.',
  'Он уже есть внутри тебя.',
  'Возможно, ты давно его не слышал.',
  'Возможно, наоборот, он постоянно пытается тебе что-то подсказать.',
  'Давай найдём его вместе.',
  'Мне понадобится всего несколько вопросов.',
  'Готов начать своё путешествие?',
];

const API_CHARACTER  = 'https://functions.poehali.dev/a58d3f5f-8515-48c8-8cb1-da5d37e5aebf';
const API_PROFILE    = 'https://functions.poehali.dev/b8c6c54b-942a-4314-bae3-b90842bc1bce';
const API_SAVE       = 'https://functions.poehali.dev/5c86a155-1ff3-43d6-a0f5-f459a2bd628e';
const API_COMPLETE   = 'https://functions.poehali.dev/a6fecb70-da06-483a-9867-bb95698d3256';

type Character = {
  name: string; title: string; description: string;
  soul: string; soul_level: number;
  mind: string; mind_level: number;
  body: string; body_level: number;
  strength: string; need: string; story: string;
  task: string; image_url: string;
};

type JourneyEntry = { day_number: number; title: string; text: string; task_date: string };
type TodayTask    = { task_text: string; completed: boolean; task_date: string };

const QUESTIONS = [
  { q: 'Как ты чувствуешь себя сегодня?', placeholder: 'Опиши своё состояние одной-двумя фразами…' },
  { q: 'Что сейчас больше всего занимает твои мысли?', placeholder: 'О чём ты думаешь чаще всего…' },
  { q: 'Что даёт тебе энергию?', placeholder: 'Люди, дела, места…' },
  { q: 'Что забирает энергию?', placeholder: 'Что утомляет или тревожит…' },
  {
    q: 'Если бы твой внутренний мир был персонажем, кто бы это был?',
    options: ['Гномик', 'Самурай', 'Путник', 'Алхимик', 'Богатырь', 'Исследователь', 'Мудрец'],
  },
  { q: 'Какой он сейчас?', options: ['Яркий', 'Уставший', 'Спокойный', 'Ищущий', 'Потерянный'] },
  { q: 'Что ему сейчас нужно больше всего?', placeholder: 'Отдых, движение, тишина, смелость…' },
  { q: 'Что ты хочешь почувствовать через 7 дней?', placeholder: 'Лёгкость, ясность, силу…' },
  { q: 'Готов ли ты сегодня сделать одно маленькое действие?', options: ['Да, я готов', 'Пока присматриваюсь'] },
];

const NAV = [
  { id: 'home',     label: 'Главная',      icon: 'Home' },
  { id: 'interview',label: 'Интервью',     icon: 'MessageCircleHeart' },
  { id: 'profile',  label: 'Персонаж',     icon: 'Sparkles' },
  { id: 'task',     label: 'Задание дня',  icon: 'CircleCheck' },
  { id: 'journey',  label: 'История',      icon: 'Footprints' },
  { id: 'contacts', label: 'Поддержка',    icon: 'LifeBuoy' },
];

const DEMO_STATES = [
  { name: 'Душа', icon: 'Heart',     value: 'Ищет тишины',         level: 64 },
  { name: 'Ум',   icon: 'Brain',     value: 'Перегружен мыслями',  level: 48 },
  { name: 'Тело', icon: 'Activity',  value: 'Хочет движения',      level: 72 },
];

type View = 'init' | 'home' | 'interview' | 'loading' | 'profile' | 'task' | 'journey' | 'contacts';

const Index = () => {
  const [view,      setView]      = useState<View>('init');
  const [step,      setStep]      = useState(0);
  const [answers,   setAnswers]   = useState<Record<number, string>>({});
  const [error,     setError]     = useState('');

  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [character,    setCharacter]    = useState<Character | null>(null);
  const [todayTask,    setTodayTask]    = useState<TodayTask | null>(null);
  const [journey,      setJourney]      = useState<JourneyEntry[]>([]);
  const [taskDone,     setTaskDone]     = useState(false);

  /* story state */
  const [visibleLines, setVisibleLines] = useState(0);
  const [storyDone,    setStoryDone]    = useState(false);
  const storyRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* ── Инициализация: сессия и загрузка профиля ── */
  useEffect(() => {
    const init = async () => {
      let token = localStorage.getItem('diagnomika_token');

      if (!token) {
        const res = await fetch(API_PROFILE, { method: 'POST' });
        const data = await res.json();
        token = data.session_token as string;
        localStorage.setItem('diagnomika_token', token);
      }

      setSessionToken(token);

      const res = await fetch(API_PROFILE, {
        headers: { 'X-Session-Token': token },
      });
      const data = await res.json();

      if (data.character) {
        setCharacter({ ...data.character, task: data.today_task?.task_text || '' });
        setTodayTask(data.today_task);
        setTaskDone(data.today_task?.completed ?? false);
        setJourney(data.journey || []);
        setView('home');
      } else {
        setView('home');
      }
    };

    init().catch(() => setView('home'));
  }, []);

  /* Story auto-play */
  useEffect(() => {
    if (view !== 'home') return;
    setVisibleLines(0);
    setStoryDone(false);
    let idx = 0;
    storyRef.current = setInterval(() => {
      idx += 1;
      setVisibleLines(idx);
      if (idx >= STORY_LINES.length) {
        clearInterval(storyRef.current!);
        setStoryDone(true);
      }
    }, 600);
    return () => { if (storyRef.current) clearInterval(storyRef.current); };
  }, [view]);

  const current  = QUESTIONS[step];
  const progress = ((step + 1) / QUESTIONS.length) * 100;

  const answer = (val: string) => setAnswers((p) => ({ ...p, [step]: val }));

  const generate = async () => {
    setError('');
    setView('loading');
    try {
      const payload = { answers: QUESTIONS.map((qq, i) => ({ q: qq.q, a: answers[i] || '' })) };
      const res = await fetch(API_CHARACTER, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('generate failed');
      const data: Character = await res.json();
      setCharacter(data);
      setTaskDone(false);

      /* Сохраняем в БД */
      if (sessionToken) {
        await fetch(API_SAVE, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-Session-Token': sessionToken },
          body: JSON.stringify({ character: data, task: data.task }),
        });

        /* Обновляем историю */
        const prof = await fetch(API_PROFILE, { headers: { 'X-Session-Token': sessionToken } });
        const profData = await prof.json();
        setJourney(profData.journey || []);
        setTodayTask(profData.today_task);
      }

      setView('profile');
    } catch {
      setError('Не удалось создать персонажа. Попробуй ещё раз.');
      setView('interview');
    }
  };

  const next = () => {
    if (step < QUESTIONS.length - 1) setStep((s) => s + 1);
    else generate();
  };

  const startInterview = () => {
    setStep(0);
    setAnswers({});
    setError('');
    setView('interview');
  };

  const completeTask = async () => {
    setTaskDone(true);
    if (sessionToken) {
      await fetch(API_COMPLETE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Session-Token': sessionToken },
        body: JSON.stringify({}),
      });
    }
  };

  const goTo = (id: string) => {
    if (id === 'interview') startInterview();
    else setView(id as View);
  };

  /* ── Данные для профиля ── */
  const states = character
    ? [
        { name: 'Душа', icon: 'Heart',    value: character.soul, level: character.soul_level },
        { name: 'Ум',   icon: 'Brain',    value: character.mind, level: character.mind_level },
        { name: 'Тело', icon: 'Activity', value: character.body, level: character.body_level },
      ]
    : DEMO_STATES;

  const charName = character ? `${character.name}, ${character.title}` : 'Альмар, Тихий Путник';
  const charDesc = character?.description ||
    'Он идёт по сумеречной тропе без спешки. В его глазах — усталость от лишнего шума и тихая надежда найти ясность.';
  const charImg     = character?.image_url || CHARACTER_IMG;
  const charStrength = character?.strength || 'Внутреннее спокойствие';
  const charNeed    = character?.need || 'Быть услышанным';
  const taskText    = character?.task || todayTask?.task_text ||
    'Выпей стакан воды и 30 секунд поблагодари своё тело за то, что оно делает для тебя.';

  /* ── Спиннер инициализации ── */
  if (view === 'init') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="relative flex h-16 w-16 items-center justify-center">
          <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-accent" />
          <Icon name="Compass" size={24} className="text-accent" />
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-background grain">
      {/* ambient glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -right-32 -top-40 h-[28rem] w-[28rem] animate-breathe rounded-full bg-accent/15 blur-3xl" />
        <div className="absolute -left-24 bottom-0 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-20 mx-auto flex max-w-5xl items-center justify-between px-6 py-6">
        <button onClick={() => setView('home')} className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <Icon name="Compass" size={18} />
          </div>
          <span className="font-display text-2xl font-semibold tracking-tight">Диагномика</span>
        </button>
        <nav className="hidden items-center gap-1 md:flex">
          {NAV.slice(1).map((n) => (
            <button
              key={n.id}
              onClick={() => goTo(n.id)}
              className={`rounded-full px-4 py-2 text-sm transition-colors ${
                view === n.id ? 'bg-secondary text-secondary-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {n.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="relative z-10 mx-auto max-w-5xl px-6 pb-32">

        {/* HOME */}
        {view === 'home' && (
          <section className="mx-auto flex max-w-4xl flex-col items-center pt-8 md:pt-12">

            {/* returning user banner */}
            {character && (
              <div className="animate-fade-in mb-8 flex w-full items-center gap-3 rounded-2xl border border-border bg-card/70 px-5 py-3 backdrop-blur-sm">
                <img src={charImg} alt="" className="h-10 w-10 rounded-full object-cover" />
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium">{character.name} ждёт тебя</p>
                  <p className="text-xs text-muted-foreground">
                    {taskDone ? 'Задание дня выполнено ✓' : 'Есть задание на сегодня'}
                  </p>
                </div>
                <Button size="sm" variant="secondary" className="rounded-full" onClick={() => setView('profile')}>
                  Открыть
                </Button>
              </div>
            )}

            {/* Two-column layout: Happy + story */}
            <div className="flex w-full flex-col items-center gap-8 md:flex-row md:items-end md:gap-12">

              {/* Happy image */}
              <div className="relative flex-shrink-0 w-64 md:w-80">
                <div className="absolute inset-0 rounded-full bg-amber-300/30 blur-3xl animate-breathe" />
                <img
                  src={HAPPY_IMG}
                  alt="Happy — внутренний персонаж"
                  className="relative w-full drop-shadow-2xl"
                  style={{ filter: 'drop-shadow(0 0 40px rgba(251,191,36,0.35))' }}
                />
              </div>

              {/* Story lines */}
              <div className="flex-1 pb-4">
                <div className="space-y-3">
                  {STORY_LINES.map((line, i) => {
                    const isVisible = i < visibleLines;
                    const isGreeting = i === 0;
                    const isQuestion = line.startsWith('«') || line.startsWith('Готов');
                    const isName = i === 1;
                    return (
                      <p
                        key={i}
                        style={{
                          opacity: isVisible ? 1 : 0,
                          transform: isVisible ? 'translateY(0)' : 'translateY(10px)',
                          transition: 'opacity 0.5s ease, transform 0.5s ease',
                        }}
                        className={
                          isGreeting
                            ? 'font-display text-3xl font-semibold md:text-4xl'
                            : isName
                            ? 'font-display text-2xl font-medium text-accent md:text-3xl'
                            : isQuestion
                            ? 'font-display text-xl italic text-accent/80 md:text-2xl'
                            : 'text-lg leading-relaxed text-foreground/80 md:text-xl'
                        }
                      >
                        {line}
                      </p>
                    );
                  })}
                </div>

                {/* CTA — появляется после последней строки */}
                <div
                  style={{
                    opacity: storyDone ? 1 : 0,
                    transform: storyDone ? 'translateY(0)' : 'translateY(16px)',
                    transition: 'opacity 0.7s ease 0.2s, transform 0.7s ease 0.2s',
                  }}
                  className="mt-10 flex flex-col gap-3 sm:flex-row"
                >
                  <Button size="lg" onClick={startInterview} className="rounded-full px-10 text-base">
                    {character ? 'Обновить персонажа' : 'Да, поехали!'}
                    <Icon name="ArrowRight" size={18} className="ml-2" />
                  </Button>
                  {character && (
                    <Button size="lg" variant="ghost" onClick={() => setView('profile')} className="rounded-full px-8 text-base">
                      Мой персонаж
                    </Button>
                  )}
                </div>

                {/* skip */}
                {!storyDone && (
                  <button
                    onClick={() => {
                      if (storyRef.current) clearInterval(storyRef.current);
                      setVisibleLines(STORY_LINES.length);
                      setStoryDone(true);
                    }}
                    className="mt-6 text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground transition-colors"
                  >
                    Пропустить
                  </button>
                )}
              </div>
            </div>
          </section>
        )}

        {/* INTERVIEW */}
        {view === 'interview' && (
          <section className="pt-8">
            {/* progress */}
            <div className="mx-auto mb-8 max-w-3xl">
              <div className="mb-2 flex items-center justify-between text-sm text-muted-foreground">
                <span>Вопрос {step + 1} из {QUESTIONS.length}</span>
                <button onClick={() => setView('home')} className="hover:text-foreground transition-colors">Выйти</button>
              </div>
              <div className="h-1 w-full overflow-hidden rounded-full bg-secondary">
                <div className="h-full rounded-full bg-accent transition-all duration-500" style={{ width: `${progress}%` }} />
              </div>
            </div>

            <div className="mx-auto flex max-w-4xl flex-col items-center gap-8 md:flex-row md:items-end">

              {/* Happy — маленький, снизу */}
              <div className="relative flex-shrink-0 w-40 md:w-52">
                <div className="absolute inset-0 rounded-full bg-amber-300/25 blur-2xl animate-breathe" />
                <img
                  src={HAPPY_IMG}
                  alt="Happy"
                  key={step}
                  className="relative w-full drop-shadow-xl animate-scale-in"
                  style={{ filter: 'drop-shadow(0 0 24px rgba(251,191,36,0.3))' }}
                />
              </div>

              {/* Question card */}
              <div key={step} className="animate-fade-in flex-1">
                {/* Speech bubble */}
                <div className="relative mb-6 rounded-3xl rounded-bl-none border border-border bg-card/80 p-6 shadow-sm backdrop-blur-sm">
                  <div className="absolute -bottom-3 left-6 h-4 w-4 rotate-45 border-b border-l border-border bg-card/80" />
                  <p className="font-display text-2xl font-medium leading-snug md:text-3xl">
                    {current.q}
                  </p>
                </div>

                {/* Answer area */}
                {current.options ? (
                  <div className="flex flex-wrap gap-3">
                    {current.options.map((o) => (
                      <button key={o} onClick={() => answer(o)}
                        className={`rounded-full border px-5 py-3 text-base transition-all ${
                          answers[step] === o
                            ? 'border-accent bg-accent text-accent-foreground shadow-sm'
                            : 'border-border bg-card/60 hover:border-accent/60 hover:bg-card'
                        }`}>
                        {o}
                      </button>
                    ))}
                  </div>
                ) : (
                  <Textarea
                    value={answers[step] || ''}
                    onChange={(e) => answer(e.target.value)}
                    placeholder={current.placeholder}
                    className="min-h-28 resize-none rounded-2xl border-border bg-card/60 p-5 text-base"
                  />
                )}

                <div className="mt-8 flex items-center justify-between">
                  <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => s - 1)} className="rounded-full">
                    <Icon name="ArrowLeft" size={18} className="mr-1" /> Назад
                  </Button>
                  <Button onClick={next} disabled={!answers[step]} className="rounded-full px-8">
                    {step === QUESTIONS.length - 1 ? 'Создать персонажа' : 'Дальше'}
                    <Icon name="ArrowRight" size={18} className="ml-1" />
                  </Button>
                </div>
                {error && <p className="mt-4 text-center text-sm text-destructive">{error}</p>}
              </div>
            </div>
          </section>
        )}

        {/* LOADING */}
        {view === 'loading' && (
          <section className="flex min-h-[60vh] flex-col items-center justify-center text-center">
            <div className="relative w-48 md:w-56">
              <div className="absolute inset-0 rounded-full bg-amber-300/30 blur-3xl animate-breathe" />
              <img
                src={HAPPY_IMG}
                alt="Happy думает…"
                className="relative w-full drop-shadow-2xl"
                style={{
                  filter: 'drop-shadow(0 0 32px rgba(251,191,36,0.4))',
                  animation: 'breathe 2s ease-in-out infinite',
                }}
              />
            </div>
            <h2 className="mt-8 font-display text-3xl font-medium md:text-4xl">
              Ищу твоего персонажа…
            </h2>
            <p className="mt-3 max-w-sm text-muted-foreground">
              Happy уже чувствует, кто живёт внутри тебя. Ещё немного — и он появится.
            </p>
            <div className="mt-6 flex gap-1.5">
              {[0,1,2].map(i => (
                <div key={i} className="h-2 w-2 rounded-full bg-accent"
                  style={{ animation: `breathe 1.2s ease-in-out ${i * 0.2}s infinite` }} />
              ))}
            </div>
          </section>
        )}

        {/* PROFILE */}
        {view === 'profile' && (
          <section className="grid gap-10 pt-8 md:grid-cols-2 md:items-center">
            <div className="animate-scale-in relative">
              <div className="absolute -inset-4 rounded-[2rem] bg-accent/15 blur-2xl" />
              <img src={charImg} alt="Внутренний персонаж"
                className="relative aspect-[4/5] w-full rounded-[2rem] object-cover shadow-2xl" />
            </div>
            <div className="animate-fade-in">
              <span className="text-sm uppercase tracking-widest text-muted-foreground">Твой персонаж</span>
              <h2 className="mt-2 font-display text-5xl font-medium tracking-tight">{charName}</h2>
              <p className="mt-5 text-lg leading-relaxed text-muted-foreground">{charDesc}</p>

              <div className="mt-8 space-y-4">
                {states.map((s) => (
                  <div key={s.name} className="rounded-2xl border border-border bg-card/70 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Icon name={s.icon} size={18} className="text-accent" />
                        <span className="font-medium">{s.name}</span>
                      </div>
                      <span className="text-sm text-muted-foreground">{s.value}</span>
                    </div>
                    <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                      <div className="h-full rounded-full bg-accent transition-all duration-700" style={{ width: `${s.level}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="rounded-2xl border border-border bg-card/70 p-4">
                  <span className="text-xs uppercase tracking-wide text-muted-foreground">Сильная сторона</span>
                  <p className="mt-1 font-display text-lg">{charStrength}</p>
                </div>
                <div className="rounded-2xl border border-border bg-card/70 p-4">
                  <span className="text-xs uppercase tracking-wide text-muted-foreground">Скрытая потребность</span>
                  <p className="mt-1 font-display text-lg">{charNeed}</p>
                </div>
              </div>

              <Button size="lg" onClick={() => setView('task')} className="mt-8 w-full rounded-full text-base">
                Задание дня <Icon name="ArrowRight" size={18} className="ml-1" />
              </Button>
            </div>
          </section>
        )}

        {/* TASK */}
        {view === 'task' && (
          <section className="mx-auto max-w-2xl pt-12 text-center">
            <span className="text-sm uppercase tracking-widest text-muted-foreground">
              Один день · Одна задача · Один результат
            </span>
            <h2 className="mt-4 font-display text-4xl font-medium md:text-5xl">Задание дня</h2>
            <div className="animate-scale-in mt-10 rounded-[2rem] border border-border bg-card/80 p-10 shadow-xl">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-accent/15">
                <Icon name="GlassWater" size={30} className="text-accent" />
              </div>
              <p className="mt-6 font-display text-2xl leading-snug md:text-3xl">{taskText}</p>
              <Button size="lg" onClick={completeTask} disabled={taskDone}
                className="mt-8 rounded-full px-10 text-base">
                {taskDone
                  ? <><Icon name="Check" size={18} className="mr-1" /> Выполнено сегодня</>
                  : 'Я сделал это'}
              </Button>
              {taskDone && (
                <p className="animate-fade-in mt-6 text-muted-foreground">
                  {character?.name || 'Персонаж'} стал чуть ярче. Возвращайся завтра — путь продолжится.
                </p>
              )}
            </div>
          </section>
        )}

        {/* JOURNEY */}
        {view === 'journey' && (
          <section className="mx-auto max-w-2xl pt-12">
            <h2 className="font-display text-4xl font-medium md:text-5xl">История развития</h2>
            <p className="mt-3 text-muted-foreground">Каждый день оставляет след на пути твоего персонажа.</p>

            {journey.length === 0 ? (
              <div className="mt-12 rounded-3xl border border-border bg-card/70 p-10 text-center">
                <Icon name="Footprints" size={32} className="mx-auto text-muted-foreground" />
                <p className="mt-4 text-muted-foreground">
                  История начнётся, как только ты создашь своего персонажа.
                </p>
                <Button className="mt-6 rounded-full" onClick={startInterview}>Начать путь</Button>
              </div>
            ) : (
              <div className="relative mt-10 space-y-6 border-l border-border pl-8">
                {journey.map((j, idx) => (
                  <div key={j.day_number} className="relative animate-fade-in">
                    <span className={`absolute -left-[2.6rem] flex h-6 w-6 items-center justify-center rounded-full ${
                      idx < journey.length - 1 ? 'bg-accent text-accent-foreground' : 'border border-border bg-card'
                    }`}>
                      {idx < journey.length - 1 && <Icon name="Check" size={14} />}
                    </span>
                    <div className="rounded-2xl border border-border bg-card/70 p-5">
                      <span className="text-xs uppercase tracking-wide text-muted-foreground">
                        День {j.day_number} · {j.task_date}
                      </span>
                      <h3 className="mt-1 font-display text-xl font-semibold">{j.title}</h3>
                      <p className="mt-1 text-muted-foreground">{j.text}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* CONTACTS */}
        {view === 'contacts' && (
          <section className="mx-auto max-w-xl pt-12 text-center">
            <h2 className="font-display text-4xl font-medium md:text-5xl">Поддержка и обратная связь</h2>
            <p className="mt-4 text-muted-foreground">
              Диагномика растёт вместе с тобой. Поделись тем, что чувствуешь, — это помогает нам делать путь добрее.
            </p>
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-border bg-card/70 p-6 text-left">
                <Icon name="Send" size={22} className="text-accent" />
                <h3 className="mt-3 font-display text-xl">Telegram</h3>
                <p className="text-sm text-muted-foreground">Напиши нам в чат сообщества</p>
              </div>
              <div className="rounded-2xl border border-border bg-card/70 p-6 text-left">
                <Icon name="Mail" size={22} className="text-accent" />
                <h3 className="mt-3 font-display text-xl">Почта</h3>
                <p className="text-sm text-muted-foreground">care@diagnomika.app</p>
              </div>
            </div>
            <Button size="lg" className="mt-8 rounded-full px-8">Написать нам</Button>
          </section>
        )}

      </main>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-4 left-1/2 z-30 flex -translate-x-1/2 gap-1 rounded-full border border-border bg-card/90 px-2 py-2 shadow-lg backdrop-blur md:hidden">
        {NAV.map((n) => (
          <button key={n.id} onClick={() => goTo(n.id)}
            className={`flex h-11 w-11 items-center justify-center rounded-full transition-colors ${
              view === n.id ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
            }`}>
            <Icon name={n.icon} size={20} />
          </button>
        ))}
      </nav>
    </div>
  );
};

export default Index;