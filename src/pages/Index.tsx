import { useState } from 'react';
import Icon from '@/components/ui/icon';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

const CHARACTER_IMG =
  'https://cdn.poehali.dev/projects/cb7818a8-cd7f-40ae-8055-7881cf09d17e/files/763ee90f-b510-426b-9358-16a0289dc20e.jpg';

const CHARACTER_API = 'https://functions.poehali.dev/a58d3f5f-8515-48c8-8cb1-da5d37e5aebf';

type Character = {
  name: string;
  title: string;
  description: string;
  soul: string;
  soul_level: number;
  mind: string;
  mind_level: number;
  body: string;
  body_level: number;
  strength: string;
  need: string;
  story: string;
  task: string;
  image_url: string;
};

const QUESTIONS = [
  { q: 'Как ты чувствуешь себя сегодня?', placeholder: 'Опиши своё состояние одной-двумя фразами…' },
  { q: 'Что сейчас больше всего занимает твои мысли?', placeholder: 'О чём ты думаешь чаще всего…' },
  { q: 'Что даёт тебе энергию?', placeholder: 'Люди, дела, места…' },
  { q: 'Что забирает энергию?', placeholder: 'Что утомляет или тревожит…' },
  {
    q: 'Если бы твой внутренний мир был персонажем, кто бы это был?',
    options: ['Гномик', 'Самурай', 'Путник', 'Алхимик', 'Богатырь', 'Исследователь', 'Мудрец'],
  },
  {
    q: 'Какой он сейчас?',
    options: ['Яркий', 'Уставший', 'Спокойный', 'Ищущий', 'Потерянный'],
  },
  { q: 'Что ему сейчас нужно больше всего?', placeholder: 'Отдых, движение, тишина, смелость…' },
  { q: 'Что ты хочешь почувствовать через 7 дней?', placeholder: 'Лёгкость, ясность, силу…' },
  {
    q: 'Готов ли ты сегодня сделать одно маленькое действие?',
    options: ['Да, я готов', 'Пока присматриваюсь'],
  },
];

const NAV = [
  { id: 'home', label: 'Главная', icon: 'Home' },
  { id: 'interview', label: 'Интервью', icon: 'MessageCircleHeart' },
  { id: 'profile', label: 'Персонаж', icon: 'Sparkles' },
  { id: 'task', label: 'Задание дня', icon: 'CircleCheck' },
  { id: 'journey', label: 'История', icon: 'Footprints' },
  { id: 'contacts', label: 'Поддержка', icon: 'LifeBuoy' },
];

const STATES = [
  { name: 'Душа', icon: 'Heart', value: 'Ищет тишины', level: 64 },
  { name: 'Ум', icon: 'Brain', value: 'Перегружен мыслями', level: 48 },
  { name: 'Тело', icon: 'Activity', value: 'Хочет движения', level: 72 },
];

const JOURNEY = [
  { day: 'День 1', title: 'Знакомство', text: 'Ты создал своего персонажа и впервые услышал его голос.', done: true },
  { day: 'День 2', title: 'Первый вдох', text: 'Минута тишины принесла ясность в начало дня.', done: true },
  { day: 'День 3', title: 'Сегодня', text: 'Персонаж ждёт твоего маленького шага.', done: false },
];

const Index = () => {
  const [view, setView] = useState<'home' | 'interview' | 'loading' | 'profile' | 'task' | 'journey' | 'contacts'>('home');
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [taskDone, setTaskDone] = useState(false);
  const [character, setCharacter] = useState<Character | null>(null);
  const [error, setError] = useState('');

  const current = QUESTIONS[step];
  const progress = ((step + 1) / QUESTIONS.length) * 100;

  const answer = (val: string) => {
    setAnswers((p) => ({ ...p, [step]: val }));
  };

  const generate = async () => {
    setError('');
    setView('loading');
    try {
      const payload = {
        answers: QUESTIONS.map((qq, i) => ({ q: qq.q, a: answers[i] || '' })),
      };
      const res = await fetch(CHARACTER_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('bad response');
      const data: Character = await res.json();
      setCharacter(data);
      setTaskDone(false);
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

  return (
    <div className="min-h-screen relative bg-background grain">
      {/* soft ambient glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-32 h-[28rem] w-[28rem] rounded-full bg-accent/15 blur-3xl animate-breathe" />
        <div className="absolute bottom-0 -left-24 h-96 w-96 rounded-full bg-primary/10 blur-3xl" />
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
              onClick={() => setView(n.id as typeof view)}
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
          <section className="flex flex-col items-center pt-12 text-center md:pt-20">
            <span className="animate-fade-in mb-6 rounded-full border border-border bg-card/60 px-4 py-1.5 text-sm text-muted-foreground">
              Персональный ИИ-навигатор образа жизни
            </span>
            <h1 className="animate-fade-in-slow max-w-3xl font-display text-5xl font-medium leading-[1.05] tracking-tight md:text-7xl">
              Любой выбор, который ты делаешь, —{' '}
              <span className="italic text-accent">правильный</span>, потому что он твой.
            </h1>
            <p className="animate-fade-in mt-8 max-w-xl text-lg leading-relaxed text-muted-foreground" style={{ animationDelay: '0.2s', opacity: 0 }}>
              Ты здесь, чтобы познакомиться с собой. Давай создадим твоего внутреннего
              персонажа, который отражает состояние твоей Души, Ума и Тела.
            </p>
            <div className="animate-fade-in mt-10 flex flex-col gap-3 sm:flex-row" style={{ animationDelay: '0.35s', opacity: 0 }}>
              <Button size="lg" onClick={startInterview} className="rounded-full px-8 text-base">
                Создать персонажа
                <Icon name="ArrowRight" size={18} className="ml-1" />
              </Button>
              <Button size="lg" variant="ghost" onClick={() => setView('profile')} className="rounded-full px-8 text-base">
                Посмотреть пример
              </Button>
            </div>

            <div className="animate-scale-in mt-20 grid w-full gap-4 sm:grid-cols-3" style={{ animationDelay: '0.5s', opacity: 0 }}>
              {[
                { icon: 'MessageCircleHeart', t: 'Короткое интервью', d: '7–10 вопросов о тебе настоящем' },
                { icon: 'Sparkles', t: 'Твой персонаж', d: 'Образ внутреннего состояния' },
                { icon: 'Footprints', t: 'Один шаг в день', d: 'Маленькое действие к себе' },
              ].map((c) => (
                <div key={c.t} className="rounded-3xl border border-border bg-card/70 p-6 text-left backdrop-blur-sm">
                  <Icon name={c.icon} size={24} className="text-accent" />
                  <h3 className="mt-4 font-display text-xl font-semibold">{c.t}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{c.d}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* INTERVIEW */}
        {view === 'interview' && (
          <section className="mx-auto max-w-2xl pt-10">
            <div className="mb-10">
              <div className="mb-3 flex items-center justify-between text-sm text-muted-foreground">
                <span>Вопрос {step + 1} из {QUESTIONS.length}</span>
                <button onClick={() => setView('home')} className="hover:text-foreground">Выйти</button>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                <div className="h-full rounded-full bg-accent transition-all duration-500" style={{ width: `${progress}%` }} />
              </div>
            </div>

            <div key={step} className="animate-fade-in">
              <h2 className="font-display text-3xl font-medium leading-tight md:text-4xl">{current.q}</h2>

              {current.options ? (
                <div className="mt-8 flex flex-wrap gap-3">
                  {current.options.map((o) => (
                    <button
                      key={o}
                      onClick={() => answer(o)}
                      className={`rounded-full border px-5 py-3 text-base transition-all ${
                        answers[step] === o
                          ? 'border-accent bg-accent text-accent-foreground'
                          : 'border-border bg-card/60 hover:border-accent/50'
                      }`}
                    >
                      {o}
                    </button>
                  ))}
                </div>
              ) : (
                <Textarea
                  value={answers[step] || ''}
                  onChange={(e) => answer(e.target.value)}
                  placeholder={current.placeholder}
                  className="mt-8 min-h-32 resize-none rounded-2xl border-border bg-card/60 p-5 text-base"
                />
              )}

              <div className="mt-10 flex items-center justify-between">
                <Button
                  variant="ghost"
                  disabled={step === 0}
                  onClick={() => setStep((s) => s - 1)}
                  className="rounded-full"
                >
                  <Icon name="ArrowLeft" size={18} className="mr-1" /> Назад
                </Button>
                <Button onClick={next} disabled={!answers[step]} className="rounded-full px-8">
                  {step === QUESTIONS.length - 1 ? 'Создать персонажа' : 'Дальше'}
                  <Icon name="ArrowRight" size={18} className="ml-1" />
                </Button>
              </div>
              {error && <p className="mt-6 text-center text-sm text-destructive">{error}</p>}
            </div>
          </section>
        )}

        {/* LOADING */}
        {view === 'loading' && (
          <section className="flex min-h-[60vh] flex-col items-center justify-center text-center">
            <div className="relative flex h-28 w-28 items-center justify-center">
              <div className="absolute inset-0 rounded-full bg-accent/20 blur-xl animate-breathe" />
              <div className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-accent" />
              <Icon name="Sparkles" size={32} className="text-accent" />
            </div>
            <h2 className="animate-fade-in mt-10 font-display text-3xl font-medium md:text-4xl">
              Твой персонаж рождается…
            </h2>
            <p className="animate-fade-in mt-3 max-w-sm text-muted-foreground">
              Я слушаю твои ответы и собираю образ Души, Ума и Тела. Это займёт около минуты.
            </p>
          </section>
        )}

        {/* PROFILE */}
        {view === 'profile' && (() => {
          const states = character
            ? [
                { name: 'Душа', icon: 'Heart', value: character.soul, level: character.soul_level },
                { name: 'Ум', icon: 'Brain', value: character.mind, level: character.mind_level },
                { name: 'Тело', icon: 'Activity', value: character.body, level: character.body_level },
              ]
            : STATES;
          const img = character?.image_url || CHARACTER_IMG;
          const name = character ? `${character.name}, ${character.title}` : 'Альмар, Тихий Путник';
          const desc = character?.description ||
            'Он идёт по сумеречной тропе без спешки. В его глазах — усталость от лишнего шума и тихая надежда найти ясность. Он не потерян, он ищет.';
          const strength = character?.strength || 'Внутреннее спокойствие';
          const need = character?.need || 'Быть услышанным';
          return (
          <section className="grid gap-10 pt-8 md:grid-cols-2 md:items-center">
            <div className="animate-scale-in relative">
              <div className="absolute -inset-4 rounded-[2rem] bg-accent/15 blur-2xl" />
              <img
                src={img}
                alt="Внутренний персонаж"
                className="relative aspect-[4/5] w-full rounded-[2rem] object-cover shadow-2xl"
              />
            </div>
            <div className="animate-fade-in">
              <span className="text-sm uppercase tracking-widest text-muted-foreground">Твой персонаж</span>
              <h2 className="mt-2 font-display text-5xl font-medium tracking-tight">{name}</h2>
              <p className="mt-5 text-lg leading-relaxed text-muted-foreground">{desc}</p>

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
                      <div className="h-full rounded-full bg-accent" style={{ width: `${s.level}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4">
                <div className="rounded-2xl border border-border bg-card/70 p-4">
                  <span className="text-xs uppercase tracking-wide text-muted-foreground">Сильная сторона</span>
                  <p className="mt-1 font-display text-lg">{strength}</p>
                </div>
                <div className="rounded-2xl border border-border bg-card/70 p-4">
                  <span className="text-xs uppercase tracking-wide text-muted-foreground">Скрытая потребность</span>
                  <p className="mt-1 font-display text-lg">{need}</p>
                </div>
              </div>

              <Button size="lg" onClick={() => setView('task')} className="mt-8 w-full rounded-full text-base">
                Получить задание дня <Icon name="ArrowRight" size={18} className="ml-1" />
              </Button>
            </div>
          </section>
          );
        })()}

        {/* TASK */}
        {view === 'task' && (
          <section className="mx-auto max-w-2xl pt-12 text-center">
            <span className="text-sm uppercase tracking-widest text-muted-foreground">Один день · Одна задача · Один результат</span>
            <h2 className="mt-4 font-display text-4xl font-medium md:text-5xl">Задание дня</h2>
            <div className="animate-scale-in mt-10 rounded-[2rem] border border-border bg-card/80 p-10 shadow-xl">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-accent/15">
                <Icon name="GlassWater" size={30} className="text-accent" />
              </div>
              <p className="mt-6 font-display text-2xl leading-snug md:text-3xl">
                {character?.task ||
                  'Выпей стакан воды и 30 секунд поблагодари своё тело за то, что оно делает для тебя.'}
              </p>
              <Button
                size="lg"
                onClick={() => setTaskDone(true)}
                disabled={taskDone}
                className="mt-8 rounded-full px-10 text-base"
              >
                {taskDone ? (
                  <>
                    <Icon name="Check" size={18} className="mr-1" /> Выполнено сегодня
                  </>
                ) : (
                  'Я сделал это'
                )}
              </Button>
              {taskDone && (
                <p className="animate-fade-in mt-6 text-muted-foreground">
                  {character?.name || 'Альмар'} стал чуть ярче. Возвращайся завтра — путь продолжится.
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
            <div className="relative mt-10 space-y-6 border-l border-border pl-8">
              {JOURNEY.map((j) => (
                <div key={j.day} className="relative animate-fade-in">
                  <span
                    className={`absolute -left-[2.6rem] flex h-6 w-6 items-center justify-center rounded-full ${
                      j.done ? 'bg-accent text-accent-foreground' : 'border border-border bg-card'
                    }`}
                  >
                    {j.done && <Icon name="Check" size={14} />}
                  </span>
                  <div className="rounded-2xl border border-border bg-card/70 p-5">
                    <span className="text-xs uppercase tracking-wide text-muted-foreground">{j.day}</span>
                    <h3 className="mt-1 font-display text-xl font-semibold">{j.title}</h3>
                    <p className="mt-1 text-muted-foreground">{j.text}</p>
                  </div>
                </div>
              ))}
            </div>
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
          <button
            key={n.id}
            onClick={() => (n.id === 'interview' ? startInterview() : setView(n.id as typeof view))}
            className={`flex h-11 w-11 items-center justify-center rounded-full transition-colors ${
              view === n.id ? 'bg-accent text-accent-foreground' : 'text-muted-foreground'
            }`}
          >
            <Icon name={n.icon} size={20} />
          </button>
        ))}
      </nav>
    </div>
  );
};

export default Index;