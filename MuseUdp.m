    classdef MuseUdp
    %MUSEUDP 
    
    properties
        udp_address
        udp_port_base
        
        udp_sock_eeg
        udp_sock_ppg
        udp_sock_acc
        udp_sock_gyro
        
        use_eeg
        use_ppg
        use_acc
        use_gyro
        udp_buffer_size = 1024;
    end
    
    properties (Constant)
        EEG_OFFSET = 0;
        PPG_OFFSET = 1;
        ACC_OFFSET = 2;
        GYRO_OFFSET = 3; 
        
        timeout = 5; % Seconds
    end
    
    methods (Hidden = false)
        function obj = MuseUdp(use_eeg, use_ppg, use_acc, use_gyro, udp_port_base)
            
            if nargin > 4
                obj.udp_port_base = udp_port_base;
            else
                obj.udp_port_base = 1963;
            end
            
            if nargin == 0
                obj.use_eeg = true;
                obj.use_ppg = true;
                obj.use_acc = true;
                obj.use_gyro = true;
            else
                obj.use_eeg = use_eeg;
                obj.use_ppg = use_ppg;
                obj.use_acc = use_acc;
                obj.use_gyro = use_gyro;
            end
            obj.udp_address = 'localhost';
            
            %try
                obj = obj.refresh_connection();
            %catch
            %    disp 'Error while establishing UDP conncetion, check permissions'
            %end
        end
        
        function obj = refresh_connection (obj)
            % Clean up already open udp ports
            udps=instrfindall;
            for u = 1:size(udps,2)
                u_port = udps(u).RemotePort;
                
                if u_port >= obj.udp_port_base && ...
                        u_port <= obj.udp_port_base+MuseUdp.GYRO_OFFSET
                    delete (udps(u))
                end    
            end
            
            % Cleaning sockets
            obj.udp_sock_eeg=[];
            obj.udp_sock_ppg=[];
            obj.udp_sock_acc=[];
            obj.udp_sock_gyro=[];
            
            % creating sockets
            if obj.use_eeg 
                
                obj.udp_sock_eeg = ...
                    udp(obj.udp_address,obj.udp_port_base+MuseUdp.EEG_OFFSET,...
                    'localport', obj.udp_port_base+MuseUdp.EEG_OFFSET);
                obj.udp_sock_eeg.Timeout = MuseUdp.timeout;
                obj.udp_sock_eeg.ByteOrder = 'littleEndian';
                obj.udp_sock_eeg.InputBufferSize = obj.udp_buffer_size;
                fopen(obj.udp_sock_eeg);
            end
            
            if obj.use_ppg 
                obj.udp_sock_ppg = ...
                    udp(obj.udp_address,obj.udp_port_base+MuseUdp.PPG_OFFSET,...
                    'localport', obj.udp_port_base+MuseUdp.PPG_OFFSET);
                obj.udp_sock_ppg.Timeout = MuseUdp.timeout;
                obj.udp_sock_ppg.ByteOrder = 'littleEndian';
                obj.udp_sock_ppg.InputBufferSize = obj.udp_buffer_size;
                fopen(obj.udp_sock_ppg);
            end
            
            if obj.use_acc 
                obj.udp_sock_acc = ...
                    udp(obj.udp_address,obj.udp_port_base+MuseUdp.ACC_OFFSET,...
                    'localport', obj.udp_port_base+MuseUdp.ACC_OFFSET);
                obj.udp_sock_acc.Timeout = MuseUdp.timeout;
                obj.udp_sock_acc.ByteOrder = 'littleEndian';
                obj.udp_sock_acc.InputBufferSize = obj.udp_buffer_size;
                fopen(obj.udp_sock_acc);
            end
            
            if obj.use_gyro 
                obj.udp_sock_gyro = ...
                    udp(obj.udp_address,obj.udp_port_base+MuseUdp.GYRO_OFFSET,...
                    'localport', obj.udp_port_base+MuseUdp.GYRO_OFFSET);
                obj.udp_sock_gyro.Timeout = MuseUdp.timeout;
                obj.udp_sock_gyro.ByteOrder = 'littleEndian';
                obj.udp_sock_gyro.InputBufferSize = obj.udp_buffer_size;
                fopen(obj.udp_sock_gyro);
            end
            
            
            
        end
        
        function [data, ts, success] = get_eeg_sample(obj)
            data = zeros([1,5]);
            ts = 0.0;
            success = false;
            
            if ~obj.use_eeg; return; end
            
            A = fread(obj.udp_sock_eeg, 6, 'single');
            
            success = ~isempty(A) && size(A,1) == 6;
            
            if ~success; return; end
            
            data = A(1:5);
            ts = A(6);
            
            return
        end
        
        function [data, ts, success] = get_ppg_sample(obj)
            data = zeros([1,3]);
            ts = 0.0;
            success = false;
            
            if ~obj.use_ppg; return; end
            
            A = fread(obj.udp_sock_ppg, 4, 'single');
            
            success = ~isempty(A) && size(A,1) == 4;
            if ~success; return; end
            
            data = A(1:3);
            ts = A(4);
            return
        end
        
        function [data, ts, success] = get_acc_sample(obj)
            data = zeros([1,3]);
            ts = 0.0;
            success = false;
            
            if ~obj.use_acc; return; end
            
            A = fread(obj.udp_sock_acc, 4, 'single');
            
            success = ~isempty(A) && size(A,1) == 4;
            if ~success; return; end % TODO: Leave them in as NaNs and let the user decide what to do with it.
            
            data = A(1:3);
            ts = A(4);
            return
        end
        
        function [data, ts, success] = get_gyro_sample(obj)
            data = zeros([1,3]);
            ts = 0.0;
            success = false;
            
            if ~obj.use_gyro; return; end
            
            A = fread(obj.udp_sock_gyro, 4, 'single');
            
            success = ~isempty(A) && size(A,1) == 4;
            if ~success; return; end
            
            data = A(1:3);
            ts = A(4);
            return
        end
        
        function [data, ts, success] = get_eeg_chunk(obj, chunk_size)
            
            data = zeros([chunk_size, 5]);
            ts = zeros([chunk_size, 1]);
            success = true;
            
            for c = 1:chunk_size
                
                [data_t, ts_t, success_t] = obj.get_eeg_sample();
                
                if ~success_t; success = false; end
                data(c,:) = data_t;
                ts(c) = ts_t;
                
            end
            return
        end
        
        function [data, ts, success] = get_ppg_chunk(obj, chunk_size)
            
            data = zeros([chunk_size, 3]);
            ts = zeros([chunk_size, 1]);
            success = true;
            
            for c = 1:chunk_size
                
                [data_t, ts_t, success_t] = obj.get_ppg_sample();
                
                if ~success_t; success = false; end
                data(c,:) = data_t;
                ts(c) = ts_t;
                
            end
            return
        end
        
        function [data, ts, success] = get_acc_chunk(obj, chunk_size)
            
            data = zeros([chunk_size, 3]);
            ts = zeros([chunk_size, 1]);
            success = true;
            
            for c = 1:chunk_size
                
                [data_t, ts_t, success_t] = obj.get_acc_sample();
                
                if ~success_t; success = false; end
                data(c,:) = data_t;
                ts(c) = ts_t;
                
            end
            return
        end
        
        function [data, ts, success] = get_gyro_chunk(obj, chunk_size)
            
            data = zeros([chunk_size, 3]);
            ts = zeros([chunk_size, 1]);
            success = true;
            
            for c = 1:chunk_size
                
                [data_t, ts_t, success_t] = obj.get_gyro_sample();
                
                if ~success_t; success = false; end
                data(c,:) = data_t;
                ts(c) = ts_t;
                
            end
            return
        end
        
        function obj = set_udp_buffer_size (obj, udp_buffer_size)
            obj.udp_buffer_size = udp_buffer_size;
            obj = obj.refresh_connection();            
        end
        
        function delete(obj)
            udps=instrfindall;
            for u = 1:size(udps,2)
                u_port = udps(u).RemotePort;
                
                if u_port >= obj.udp_port_base && ...
                        u_port <= obj.udp_port_base+MuseUdp.GYRO_OFFSET
                    delete (udps(u))
                end    
            end
        end
        
    end

end

