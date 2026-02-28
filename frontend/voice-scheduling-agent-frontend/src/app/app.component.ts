import { Component, OnInit, OnDestroy, ChangeDetectorRef, inject } from '@angular/core';
import { NgIf, NgFor, NgClass } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import Vapi from '@vapi-ai/web';                    // ✅ direct npm import
import { environment } from '../environments/environment';

type CallStatus = 'idle' | 'connecting' | 'active' | 'ending' | 'ended';

interface TranscriptMessage {
  role: 'user' | 'assistant';
  text: string;
}

interface CalendarEvent {
  name: string;
  date: string;
  time: string;
  title: string;
  event_link?: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [NgIf, NgFor, NgClass],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent implements OnInit, OnDestroy {

  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);

  // ── State ────────────────────────────────────────────────────────────────
  callStatus: CallStatus = 'idle';
  isMuted = false;
  isAuthenticated = false;
  isCheckingAuth = true;
  isAssistantSpeaking = false;
  isUserSpeaking = false;
  isSdkReady = false;
  volumeLevel = 0;
  callDuration = 0;
  errorMessage = '';

  transcript: TranscriptMessage[] = [];
  createdEvent: CalendarEvent | null = null;

  private vapi!: Vapi;                              // ✅ typed directly
  private durationInterval?: ReturnType<typeof setInterval>;

  authFeatures = [
    'Read and write Google Calendar events',
    'Send calendar invites to clients',
    'Secure OAuth 2.0 — revoke anytime',
  ];
  
  capabilities = [
    { icon: '📞', text: 'Calls prospects and introduces Vikara' },
    { icon: '🧠', text: 'Qualifies their AI needs naturally' },
    { icon: '📅', text: 'Books discovery sessions via voice' },
    { icon: '📧', text: 'Sends Google Calendar invite instantly' },
    { icon: '🔄', text: 'Retries if booking fails' },
  ];

  // ── Lifecycle ─────────────────────────────────────────────────────────────
  ngOnInit(): void {
    this.checkAuthStatus();
    this.initVapi();            // ✅ no more CDN loading needed
  }

  ngOnDestroy(): void {
    this.endCall();
    if (this.durationInterval) clearInterval(this.durationInterval);
  }

  // ── Auth ──────────────────────────────────────────────────────────────────
  checkAuthStatus(): void {
    this.http.get<{ authenticated: boolean }>(`${environment.apiUrl}/auth/status`)
      .subscribe({
        next: (res) => {
          this.isAuthenticated = res.authenticated;
          this.isCheckingAuth = false;
          this.cdr.detectChanges();
        },
        error: () => {
          this.isCheckingAuth = false;
          this.cdr.detectChanges();
        },
      });
  }

  connectGoogle(): void {
    this.http.get<{ auth_url: string }>(`${environment.apiUrl}/auth/google`)
      .subscribe({
        next: (res) => window.location.href = res.auth_url,
        error: () => this.errorMessage = 'Failed to initiate Google authentication.',
      });
  }

  logout(): void {
    this.http.post(`${environment.apiUrl}/auth/logout`, {})
      .subscribe({
        next: () => {
          this.isAuthenticated = false;
          this.callStatus = 'idle';
          this.transcript = [];
          this.createdEvent = null;
          this.errorMessage = '';
          this.cdr.detectChanges();
        },
        error: () => {
          // Clear locally even if request fails
          this.isAuthenticated = false;
          this.cdr.detectChanges();
        }
      });
  }

  // ── VAPI Init ─────────────────────────────────────────────────────────────
  initVapi(): void {
    try {
      this.vapi = new Vapi(environment.vapiPublicKey);
      this.isSdkReady = true;
      this.setupVapiListeners();
      console.log('VAPI initialized successfully');
      this.cdr.detectChanges();
    } catch (e) {
      console.error('VAPI init error:', e);
      this.errorMessage = 'Failed to initialize voice service.';
      this.cdr.detectChanges();
    }
  }

  // ── VAPI Listeners ────────────────────────────────────────────────────────
  setupVapiListeners(): void {
    this.vapi.on('call-start', () => {
      this.callStatus = 'active';
      this.startDurationTimer();
      this.cdr.detectChanges();
    });

    this.vapi.on('call-end', () => {
      this.callStatus = 'ended';
      this.stopDurationTimer();
      this.cdr.detectChanges();
    });

    this.vapi.on('speech-start', () => {
      this.isAssistantSpeaking = true;
      this.cdr.detectChanges();
    });

    this.vapi.on('speech-end', () => {
      this.isAssistantSpeaking = false;
      this.cdr.detectChanges();
    });

    this.vapi.on('volume-level', (volume: number) => {
      this.volumeLevel = volume;
      this.cdr.detectChanges();
    });

    this.vapi.on('message', (message: any) => {
      if (message.type === 'transcript' && message.transcriptType === 'final') {
        this.transcript.push({
          role: message.role,
          text: message.transcript,
        });
        this.cdr.detectChanges();
      }

      if (message.type === 'tool-calls') {
        const fn = message.toolCallList?.[0]?.function;
        if (fn?.name === 'book_appointment') {
          const args = typeof fn.arguments === 'string'
            ? JSON.parse(fn.arguments)
            : fn.arguments;
          this.createdEvent = {
            name:  args.name,
            date:  args.date,
            time:  args.time,
            title: args.purpose,
          };
          this.cdr.detectChanges();
        }
      }

      if (message.type === 'tool-call-result') {
        const link = message.result?.event_details?.event_link;
        if (link && this.createdEvent) {
          this.createdEvent.event_link = link;
          this.cdr.detectChanges();
        }
      }
    });

    this.vapi.on('error', (error: any) => {
      console.error('VAPI error:', error);
      this.errorMessage = `Voice error: ${error.message || 'Unknown error'}`;
      this.callStatus = 'idle';
      this.cdr.detectChanges();
    });
  }

  // ── Call Controls ─────────────────────────────────────────────────────────
  async startCall(): Promise<void> {
    if (!this.isSdkReady || !this.vapi) {
      this.errorMessage = 'Voice service not ready. Please refresh.';
      return;
    }
  
    this.callStatus = 'connecting';
    this.transcript = [];
    this.createdEvent = null;
    this.errorMessage = '';
  
    try {
      const response = await this.http
        .post<{ call_id: string; assistant_id: string; web_call_url: string }>(
          `${environment.apiUrl}/call/start`, {}
        )
        .toPromise();
  
      console.log('Call response:', response);
  
      if (!response?.assistant_id) {
        throw new Error('No assistant ID received from server');
      }
  
      // ✅ Pass assistantId UUID — this is what VAPI SDK expects
      await this.vapi.start(response.assistant_id);
  
    } catch (error: any) {
      console.error('Start call error:', error);
      this.errorMessage = `Failed to start call: ${error.message || 'Unknown error'}`;
      this.callStatus = 'idle';
      this.cdr.detectChanges();
    }
  }
  
  endCall(): void {
    if (this.vapi && (this.callStatus === 'active' || this.callStatus === 'connecting')) {
      this.callStatus = 'ending';
      this.vapi.stop();
    }
  }

  toggleMute(): void {
    if (this.vapi) {
      this.isMuted = !this.isMuted;
      this.vapi.setMuted(this.isMuted);
    }
  }

  resetCall(): void {
    this.callStatus = 'idle';
    this.transcript = [];
    this.createdEvent = null;
    this.errorMessage = '';
    this.callDuration = 0;
  }

  // ── Timer ─────────────────────────────────────────────────────────────────
  startDurationTimer(): void {
    this.callDuration = 0;
    this.durationInterval = setInterval(() => {
      this.callDuration++;
      this.cdr.detectChanges();
    }, 1000);
  }

  stopDurationTimer(): void {
    if (this.durationInterval) clearInterval(this.durationInterval);
  }

  // ── Getters ───────────────────────────────────────────────────────────────
  get formattedDuration(): string {
    const m = Math.floor(this.callDuration / 60).toString().padStart(2, '0');
    const s = (this.callDuration % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  get statusLabel(): string {
    const labels: Record<CallStatus, string> = {
      idle:       'Ready to Schedule',
      connecting: 'Connecting...',
      active:     'Call Active',
      ending:     'Ending Call...',
      ended:      'Call Ended',
    };
    return labels[this.callStatus];
  }
}